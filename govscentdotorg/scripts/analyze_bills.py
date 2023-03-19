import datetime
import os

from govscentdotorg.models import Bill, BillTopic
import openai


def extract_response_topics(response: str) -> [str]:
    [top_10_index, is_single_topic] = get_top_10_index(response)
    lines = response[top_10_index:].splitlines()
    if is_single_topic:
        if len(lines[0]) > 10:
            # Example: Topic: A sunny day in canada
            return [lines[0].replace("Topic:", "").strip()]
        else:
            line = lines[1]
            if line.isnumeric():
                # Example: 1. H.R. 5889 - a bill introduced in the House of Representatives.
                first_period_index = line.index(".")
                line_after_first_number = line[first_period_index + 1:].strip()
                return [line_after_first_number]
            else:
                return line.strip()
    else:
        topics = []
        for line in lines[1:10]:
            if len(line) > 2:
                if line[0].isnumeric():
                    # Example: 1. H.R. 5889 - a bill introduced in the House of Representatives.
                    first_period_index = line.index(".")
                    line_after_first_number = line[first_period_index + 1:].strip()
                    topics.append(line_after_first_number)
                else:
                    # end of topics
                    break
        return topics


def get_topic_by_text(text: str) -> BillTopic:
    topic = BillTopic.objects.filter(name__exact=text).first()
    if topic is None:
        topic = BillTopic(name=text, created_at=datetime.datetime.now(tz=datetime.timezone.utc))
        topic.save()
        return topic
    return topic


def set_topics(bill: Bill, response: str):
    topic_texts = extract_response_topics(response)
    topics = []
    for topic_text in topic_texts:
        topic = get_topic_by_text(topic_text)
        topics.append(topic)
    bill.topics.set(topics)


# Gets the index and whether we're dealing with a single topic in the response.
def get_top_10_index(response: str) -> (int, bool):
    # noinspection PyBroadException
    try:
        index = response.index("Top 10")
        return index, False
    except ValueError:
        try:
            index = response.index("Topic:")
            return index, True
        except ValueError:
            if response[:2] == "1.":
                return 0, False
            else:
                raise ValueError


def set_focus_and_summary(bill: Bill, response: str):
    # if ValueError is thrown, we'll get an exception and openai response stored in the Bill and we can investigate later.
    # Example: Ranking on staying on topic: 10/10.
    # Very dirty and naughty but fast.
    topic_ranking_end_token = "/10"
    topic_ranking_index = response.index(topic_ranking_end_token)
    topic_ranking = response[topic_ranking_index - 2:topic_ranking_index].strip()
    bill.on_topic_ranking = topic_ranking
    top_10_index = get_top_10_index(response)[0]

    try:
        summary_token = "Summary:"
        summary_index = response.index(summary_token) + len(summary_token)
        # We assume everything after topic ranking is the summary.
        bill.text_summary = response[summary_index:top_10_index].strip()

        if summary_index < topic_ranking_index and len(response[topic_ranking_index:]) > 50:
            bill.on_topic_reasoning = response[topic_ranking_index + (len(topic_ranking_end_token)):].strip()
            if bill.on_topic_reasoning[0] == "." or bill.on_topic_reasoning[1] == ".":
                bill.on_topic_reasoning = bill.on_topic_reasoning[bill.on_topic_reasoning.index(" "):].strip()
    except ValueError:
        # Text did not contain "Summary:". So, maybe it's in the format of <topics>\n\n<ranking><summary>
        bill.text_summary = response[topic_ranking_index + 1:].strip()
        # TODO set reasoning


def analyze_bill(bill: Bill, ai_text: str):
    # Save here in case the next steps error out so we can debug.
    # Only save last_analyze_response as an optimization.
    bill.save(update_fields=['last_analyze_response'])
    set_topics(bill, ai_text)
    set_focus_and_summary(bill, ai_text)
    bill.last_analyzed_at = datetime.datetime.now(tz=datetime.timezone.utc)
    bill.last_analyze_error = None
    # Now just save everything.
    bill.save()


def run(arg_reparse_only: str):
    reparse_only = arg_reparse_only == 'True'

    if not reparse_only:
        openai.organization = os.getenv("OPENAI_API_ORG")
        openai.api_key = os.getenv("OPENAI_API_KEY")

    print('Finding bills to analyze...')
    bills = Bill.objects.filter(is_latest_revision=True, last_analyzed_at__isnull=False) \
        .only("id", "gov_id", "text") if reparse_only else Bill.objects.filter(
        is_latest_revision=True, last_analyzed_at__isnull=True).only("id", "gov_id", "text")

    print(f"Will analyze {len(bills)} bills.")
    for bill in bills:
        print(F"Analyzing {bill.gov_id}")
        # print(f"Analyzing {bill.text}")
        try:
            if not reparse_only:
                # This is done all in one prompt to try to reduce # of tokens.
                prompt = f"Summarize and list the top 10 most important topics the following text, and rank it from 0 to 10 on staying on topic:\n{bill.text}"
                completion = openai.ChatCompletion.create(model="gpt-3.5-turbo", messages=[
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": prompt}
                ])
                print(completion)
                response_text = completion.choices[0].message.content
                bill.last_analyze_response = response_text
                analyze_bill(bill, response_text)
            elif bill.last_analyze_response is not None:
                analyze_bill(bill, bill.last_analyze_response)

        except Exception as e:
            print(f"Failed for {bill.gov_id}", e)
            bill.last_analyze_error = str(e)
            bill.save(update_fields=['last_analyze_error'])
