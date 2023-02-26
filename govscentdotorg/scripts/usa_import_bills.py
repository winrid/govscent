# Import's Bills from the US Congress scraped via the Congress tool: https://github.com/unitedstates/congress
# We currently only store and analyze the most recent version.

from os import scandir, path

from govscentdotorg.models import Bill
from zipfile import ZipFile


def iterate_bills(data_dir):
    for congress_entry in scandir(data_dir):
        if congress_entry.name.startswith('.') or not congress_entry.is_dir():
            continue
        for bill_type_one in scandir(path.join(data_dir, congress_entry.name, "bills")):
            if bill_type_one.name.startswith('.') or not bill_type_one.is_dir():
                continue
            for bill_type_two in scandir(path.join(data_dir, congress_entry.name, "bills", bill_type_one.name)):
                if bill_type_two.name.startswith('.') or not bill_type_two.is_dir():
                    continue
                for bill_number in scandir(path.join(
                        data_dir,
                        congress_entry.name, "bills", bill_type_one.name, bill_type_two.name,
                )):
                    if bill_number.name.startswith('.') or not bill_number.is_dir():
                        continue
                    text_versions_dir = path.join(
                        data_dir,
                        congress_entry.name,
                        "bills",
                        bill_type_one.name,
                        bill_type_two.name,
                        "text-versions"
                    )
                    for status_code in scandir(text_versions_dir):
                        if status_code.name.startswith('.') or not status_code.is_dir():
                            continue
                        yield {
                            "congress": congress_entry.name,
                            "bill_type": bill_type_one.name,
                            "bill_type_two": bill_type_two.name, # no idea what this is
                            "bill_number": bill_number.name,
                            "status_code": status_code.name,
                            "package_zip_path": path.join(text_versions_dir, "package.zip")
                        }


def run(data_dir):
    if not data_dir:
        raise Exception("--data-dir is required.")

    for bill_dir_info in iterate_bills(data_dir):
        print(bill_dir_info)
        # with ZipFile(file_name, 'r') as zip:
        #     files = zip.filelist
        #     # find
        #     # Bill.objects.create(gov_id=)
