# Import's Bills from the US Congress scraped via the Congress tool: https://github.com/unitedstates/congress
# We currently only store and analyze the most recent version.
from encodings.utf_8 import decode

import dateutil.parser
import xml.etree.ElementTree as ET

from govscentdotorg.models import Bill
from zipfile import ZipFile, BadZipFile

from govscentdotorg.scripts.utils.pattern_iterate import iterate_dir_for_pattern


def get_bill_meta(zip: ZipFile) -> dict:
    meta = {
        "title": None,
        "date": None
    }
    # I haven't seen JSON metadata yet, only XML. If we can get the JSON, maybe use that as parsing should be faster.
    mods = next(
        (file for file in zip.filelist if file.filename.endswith('mods.xml')),
        None
    )
    if mods is not None:
        root = ET.fromstring(zip.read(mods))
        meta['title'] = root.find('./{*}titleInfo/{*}title').text
        meta['date'] = dateutil.parser.parse(root.find('./{*}originInfo/{*}dateIssued').text)

    if meta['title'] is None:
        raise Exception("Could not determine bill title.")
    if meta['date'] is None:
        raise Exception("Could not determine bill date.")
    return meta


def get_bill_html(zip: ZipFile) -> str | None:
    html = None

    html_file = next(
        # I only see .htm, but add .html just in case.
        (file for file in zip.filelist if file.filename.endswith('.htm') or file.filename.endswith('.html')),
        None
    )

    if html_file is not None:
        html = decode(zip.read(html_file))[0]

    return html


def run(data_dir):
    if not data_dir:
        raise Exception("--data-dir is required.")
    for bill_dir_info in iterate_dir_for_pattern(data_dir,
                                                 "[congress]/bills/[bill_type]/[bill_type_and_number]/text-versions/[status_code]/[package]",
                                                 0, {}):
        print(bill_dir_info)
        package_path = bill_dir_info.get('package')
        if package_path is None:
            continue
        print('Checking', package_path)
        gov_id = bill_dir_info.get('congress') + bill_dir_info.get('bill_type_and_number') + bill_dir_info.get(
            'status_code')
        existing_bill = Bill.objects.filter(gov="USA", gov_id=gov_id).only("id").first()
        if not existing_bill:
            print('Ingesting', package_path)
            try:
                zip_file = ZipFile(package_path, 'r')
                meta = get_bill_meta(zip_file)
                bill = Bill.objects.create(
                    gov="USA",
                    gov_id=gov_id,
                    title=meta.get('title'),
                    type=bill_dir_info['bill_type'],
                    html=get_bill_html(zip_file),
                    date=meta.get('date')
                )
                bill.save()
            except BadZipFile:
                print("Failed to handle bill due to it being an invalid zip file, continuing.", package_path)
        else:
            print("Bill exists, skipping...")
