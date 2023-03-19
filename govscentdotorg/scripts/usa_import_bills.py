# Import's Bills from the US Congress scraped via the Congress tool: https://github.com/unitedstates/congress
# We currently only store and analyze the most recent version.
# It takes arguments: <input_data_dir> <True/False: Whether to update all bill text> <True/False: Whether to update all bill html>
import subprocess
from encodings.utf_8 import decode
from shutil import rmtree

import dateutil.parser
import xml.etree.ElementTree as ET

from govscentdotorg.models import Bill
from zipfile import ZipFile, BadZipFile

from govscentdotorg.scripts.utils.pattern_iterate import iterate_dir_for_pattern


def get_bill_meta(zipfile: ZipFile) -> dict:
    meta = {
        "title": None,
        "date": None
    }
    # I haven't seen JSON metadata yet, only XML. If we can get the JSON, maybe use that as parsing should be faster.
    mods = next(
        (file for file in zipfile.filelist if file.filename.endswith('mods.xml')),
        None
    )
    if mods is not None:
        root = ET.fromstring(zipfile.read(mods))
        meta['title'] = root.find('./{*}titleInfo/{*}title').text
        meta['date'] = dateutil.parser.parse(root.find('./{*}originInfo/{*}dateIssued').text)

    if meta['title'] is None:
        raise Exception("Could not determine bill title.")
    if meta['date'] is None:
        raise Exception("Could not determine bill date.")
    return meta


def get_bill_text(zipfile: ZipFile) -> str | None:
    html_file = next(
        # I only see .htm, but add .html just in case.
        (file for file in zipfile.filelist if file.filename.endswith('.htm') or file.filename.endswith('.html')),
        None
    )

    if html_file is not None:
        pre_wrapped_html = decode(zipfile.read(html_file))[0]
        # Find bill text after beginning section etc
        return pre_wrapped_html.replace("<html><body><pre>", "").replace("</pre></body></html>", "").replace("\x00", "\uFFFD")
        # The below implementation was an attempt to extract text from different sections, but it does not work yet.
        # The bill format is very inconsistent. Examples - compare 114hr208eas (no separators) vs 114sconres16rfh (section separators)
        # We look for text after the 2nd _______________________________________________________________________ and
        # before the </pre>
        # bill_body = ""
        # separator = "_______" # shortened as optimization
        # found_header_start = False
        # found_header_end = False
        # for line in pre_wrapped_html.splitlines():
        #     if found_header_end:
        #         if line.startswith("</pre"):
        #             break
        #         else:
        #             bill_body += line + "\n"
        #     elif found_header_start:
        #         if line.startswith(separator):
        #             found_header_end = True
        #     elif line.startswith(separator):
        #         found_header_start = True
        # return bill_body
    return None


def get_bill_html(zipfile: ZipFile) -> str | None:
    pdf_file = next(
        # I only see .htm, but add .html just in case.
        (file for file in zipfile.filelist if file.filename.endswith('.pdf')),
        None
    )

    if pdf_file is not None:
        working_dir = "/tmp/bills_working"
        pdf_file_path = zipfile.extract(pdf_file, path=working_dir)

        command = f'pdftohtml "{pdf_file_path}" -s -noframes -i -nomerge -nodrm -stdout'
        html = subprocess.getoutput(command)

        # save disk space, keep content in zip files most of the time.
        rmtree(working_dir)

        # We only want the HTML inside the <body> tag. Everything in the <head> are not needed.
        # We could replace this with a regex, it'll probably be faster. DOM libraries are slow, and our
        # use case is simple. This is "fast enough" for now.
        in_body = False
        body_html = ""
        for line in html.splitlines():
            if in_body:
                if line.startswith("</body"):
                    break
                else:
                    body_html += line + "\n"
            elif line.startswith("<body"):
                in_body = True
        return body_html.replace("\x00", "\uFFFD")

    return None


def recalculate_latest_revision_for_group(bill: Bill):
    # While not super efficient this approach is simple and may not be a problem considering we are dealing with a small number (< 1 million) docs.
    # It is also only ran when a bill is added to a group.
    existing_bills = Bill.objects.filter(gov=bill.gov, gov_group_id=bill.gov_group_id).only("is_latest_revision", "date")
    newest = None
    for bill in existing_bills:
        if newest is None or bill.date > newest.date:
            newest = bill
    # TODO This could be done within a transaction to improve accuracy.
    newest.is_latest_revision = True
    newest.save(update_fields=["is_latest_revision"])
    if len(existing_bills) > 1:
        for bill in existing_bills:
            if bill.id != newest.id and bill.is_latest_revision:
                bill.is_latest_revision = False
                bill.save(update_fields=["is_latest_revision"])

def run(data_dir: str, update_all_text: str, update_all_html: str, update_all_cache: str):
    if not data_dir:
        raise Exception("--data-dir is required.")
    should_update_all_text = update_all_text == 'True'
    should_update_all_html = update_all_html == 'True'
    should_update_all_cache = update_all_cache == 'True'
    count_added = 0
    count_updated = 0
    for bill_dir_info in iterate_dir_for_pattern(data_dir,
                                                 "[congress]/bills/[bill_type]/[bill_type_and_number]/text-versions/[status_code]/[package]",
                                                 0, {}):
        # print(bill_dir_info)
        package_path = bill_dir_info.get('package')
        if package_path is None:
            continue
        gov_group_id = bill_dir_info.get('congress') + bill_dir_info.get('bill_type_and_number')
        gov_id = gov_group_id + bill_dir_info.get('status_code')
        print('Checking', gov_id, package_path)
        # Update the cached the latest revision.
        existing_bill = Bill.objects.filter(gov="USA", gov_id=gov_id).only("id", "gov_group_id").first()
        try:
            if not existing_bill:
                print('Ingesting', gov_id, package_path, bill_dir_info)
                zip_file = ZipFile(package_path, 'r')
                meta = get_bill_meta(zip_file)
                bill = Bill.objects.create(
                    gov="USA",
                    gov_group_id=gov_group_id,
                    gov_id=gov_id,
                    title=meta.get('title'),
                    type=bill_dir_info['bill_type'],
                    text=get_bill_text(zip_file),
                    html=get_bill_html(zip_file),
                    date=meta.get('date')
                )
                bill.save()
                recalculate_latest_revision_for_group(bill)
                count_added += 1
            else:
                # Migrate to add gov_group_id. Can remove later.
                if not existing_bill.gov_group_id:
                    existing_bill.gov_group_id = gov_group_id
                    existing_bill.save(update_fields=["gov_group_id"])
                if should_update_all_text or should_update_all_html:
                    zip_file = ZipFile(package_path, 'r')
                    if should_update_all_text:
                        print("Updating bill text...")
                        text = get_bill_text(zip_file)
                        existing_bill.text = text

                    if should_update_all_html:
                        print("Updating bill html...")
                        html = get_bill_html(zip_file)
                        existing_bill.html = html
                    existing_bill.save()
                    count_updated += 1
                else:
                    print("Bill exists, skipping...")
                if should_update_all_cache:
                    recalculate_latest_revision_for_group(existing_bill)
        except BadZipFile:
            print("Failed to handle bill due to it being an invalid zip file, continuing.", package_path)
        except UnicodeDecodeError:
            print("Failed to handle bill due to a unicode error. continuing.", package_path)
    print(f'Added {count_added} bills. Updated {count_updated} bills text.')
