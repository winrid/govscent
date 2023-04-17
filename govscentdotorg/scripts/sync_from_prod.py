# This script will populate your local setup with:
# 1. All topics from prod.
# 2. The last N bills.
# NOTE! This will override any bills you have locally if the gov_id is the same.
# Arguments: <optional_number_of_bills> <optional_bill_pk_id>
# We can fetch 1000 bills: runscript sync_from_prod --script-args 1000
# Or a specific bill: runscript sync_from_prod --script-args 1 123456

import requests
from django.db import transaction

from govscentdotorg.models import Bill, BillTopic, BillSection, BillSmell


def ingest_bill(bill_json):
    with transaction.atomic():
        # If the bill exists, delete it.
        existing_bill = Bill.objects.filter(gov=bill_json['gov'], gov_id=bill_json['gov_id']).first()
        if existing_bill is not None:
            existing_bill.delete()

        # Ingest topics.
        bill_topics = []
        for topic_json in bill_json['topics']:
            topic = BillTopic.objects.filter(name__exact=topic_json['name']).first()
            if topic is None:
                topic = BillTopic(
                    name=topic_json['name'],
                    created_at=topic_json['created_at'],
                )
                topic.save()
                bill_topics.append(topic)
            else:
                bill_topics.append(topic)

        # Ingest sections.
        bill_sections = []
        for section_json in bill_json['bill_sections']:
            section = BillSection(
                text=section_json['text'],
                last_analyze_model=section_json['last_analyze_model'],
                last_analyze_error=section_json['last_analyze_error'],
                last_analyze_response=section_json['last_analyze_response'],
            )
            section.save()
            bill_sections.append(section)

        # Ingest smells.
        bill_smells = []
        for smell_json in bill_json['smells']:
            smell = BillSmell(
                name=smell_json['name'],
                weight=smell_json['weight'],
                description=smell_json['description'],
            )
            smell.save()
            bill_smells.append(smell)

        bill_model = Bill(
            gov=bill_json['gov'],
            gov_id=bill_json['gov_id'],
            gov_group_id=bill_json['gov_group_id'],
            is_latest_revision=bill_json['is_latest_revision'],
            title=bill_json['title'],
            type=bill_json['type'],
            source_file_path=bill_json['source_file_path'],
            text=bill_json['text'],
            date=bill_json['date'],
            last_analyzed_at=bill_json['last_analyzed_at'],
            last_analyze_error=bill_json['last_analyze_error'],
            last_analyze_response=bill_json['last_analyze_response'],
            final_analyze_response=bill_json['final_analyze_response'],
            last_analyze_model=bill_json['last_analyze_model'],
            # bill_sections set later
            # topics set later
            text_summary=bill_json['text_summary'],
            # smells set later
            on_topic_ranking=bill_json['on_topic_ranking'],
            on_topic_reasoning=bill_json['on_topic_reasoning'],
            smelliness=bill_json['smelliness'],
        )
        bill_model.save()
        bill_model.topics.set(bill_topics)
        bill_model.bill_sections.set(bill_sections)
        bill_model.smells.set(bill_smells)
        bill_model.save()


def run(num_target_bills: str | None = 1_000, bill_pk_id: str | None = None):
    if bill_pk_id is not None:
        print(f"Fetching bill {bill_pk_id}.")
        response = requests.get(f"https://govscent.org/api/bills/v1/{bill_pk_id}?format=json")
        print(f"Importing bill {bill_pk_id}.")
        response_json = response.json()
        ingest_bill(response_json)
    else:
        num_bills_ingested = 0
        num_target_bills_int = int(num_target_bills)
        page = 1
        while num_bills_ingested < num_target_bills_int:
            # TODO this gets the oldest 1000 bills, fix API ordering so we can get newest.
            print('Fetching next page of bills...')
            response = requests.get(f"https://govscent.org/api/bills/v1/?format=json&page={page}")
            response_json = response.json()
            for bill_json in response_json['results']:
                print(f"Importing bill {bill_json['gov_id']} {num_bills_ingested}/{num_target_bills_int}.")
                ingest_bill(bill_json)
                num_bills_ingested += 1
            page += 1
    print('Done.')
