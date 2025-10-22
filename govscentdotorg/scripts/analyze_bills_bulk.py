# Performs analysis concurrently by running analyze_bills for every year that contains bills in the DB.
# Note that this might be very expensive for you (for example, 1993 to 2023 is about $3k USD w/ current OpenAI pricing).
import time
from subprocess import Popen, PIPE

from django.db.models.functions import TruncMonth

from govscentdotorg.models import Bill


def run():
    print('Finding year buckets...')
    bill_years = Bill.objects \
        .filter(is_latest_revision=True, last_analyzed_at__isnull=True) \
        .annotate(year=TruncMonth('date')) \
        .values('year') \
        .order_by('year') \
        .values('year')

    # This could be optimized. I don't know the Django ORM well enough to find an alternative to distinct() that works
    # with the local sqlite db.

    years = {}
    for bill_year in bill_years:
        year = bill_year['year'].year
        if year not in years:
            years[year] = True

    print(f'Running for {len(years)} year buckets.')

    processes = [
        Popen([f'python3 manage.py runscript analyze_bills --script-args False {year}'], shell=True, stdout=PIPE, stderr=PIPE)
        for year in years
    ]

    while processes:
        print(f'{len(processes)} Processes still running.')
        for proc in processes:
            return_code = proc.poll()
            if return_code is not None:  # Process finished.
                processes.remove(proc)
                break
            else:  # No process is done, wait a bit and check again.
                time.sleep(1)
                continue
