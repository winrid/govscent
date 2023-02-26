# Import's Bills from the US Congress scraped via the Congress tool: https://github.com/unitedstates/congress
# We currently only store and analyze the most recent version.

from os import scandir, path

from govscentdotorg.models import Bill
from zipfile import ZipFile

from govscentdotorg.scripts.utils.pattern_iterate import iterate_dir_for_pattern


def run(data_dir):
    if not data_dir:
        raise Exception("--data-dir is required.")
    for bill_dir_info in iterate_dir_for_pattern(data_dir, "[congress]/bills/[bill_type]/[bill_type_and_number]/text-versions/[status_code]/[package]", 0, {}):
        print(bill_dir_info)
        # with ZipFile(file_name, 'r') as zip:
        #     files = zip.filelist
        #     # find
        #     # Bill.objects.create(gov_id=)
