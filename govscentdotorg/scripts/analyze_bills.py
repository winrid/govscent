# 1. Use an existing model, since we want to determine topic similarity and our bills' content might throw this off...
# 2. Once we have topics and a way to calculate distance, we can parse our documents and use BERT's find_topics and find min/max/avg topic distance.
# 3. Topic distances, and distance from bill label, can be used to determine smelliness.

from bertopic import BERTopic
from bertopic.representation import TextGeneration
from sklearn.datasets import fetch_20newsgroups
from sklearn.metrics.pairwise import cosine_similarity

from govscentdotorg.models import Bill


def get_similarity(model: BERTopic, topic_id_1: int, topic_id_2: int) -> float:
    """Calculate the similarity between two topics.

    Returns
    -------
    float
        A similarity score between 0 and 1, where 0 is completely dissimilar and 1 is identical.
    """
    if topic_id_1 >= len(model.topic_embeddings_) or topic_id_2 >= len(model.topic_embeddings_):
        raise ValueError(f"Topics with IDs {topic_id_1} and/or {topic_id_2} do not exist.")
    topic_embedding_1 = model.topic_embeddings_[topic_id_1]
    topic_embedding_2 = model.topic_embeddings_[topic_id_2]
    return cosine_similarity([topic_embedding_1], [topic_embedding_2])[0][0]

def describe_topic():
    prompt = "I have a topic described by the following keywords: [KEYWORDS]. Based on the previous keywords, what is this topic about?"

    # Create your representation model
    generator = pipeline('text2text-generation', model='google/flan-t5-base')
    representation_model = TextGeneration(generator, prompt)
    print(representation_model.extract_topics())

def get_trained_model():
    name = ".model_newsgroups_0"
    try:
        return BERTopic.load(name)
    except FileNotFoundError:
        # Instantiate BERTopic with default parameters
        print("Instantiating BERTopic...")
        model = BERTopic(
            # Since we're analyzing one document at a time, we need a small topic size.
            min_topic_size=3
        )

        print("Getting model...")
        docs = fetch_20newsgroups(subset='all')['data']
        print("Training model...")
        trained_model = model.fit(docs)
        trained_model.save(name)
        return trained_model

def run():
    trained_model = get_trained_model()

    print("Getting bills...")
    # In the future we will only analyze things that have not yet been analyzed.
    # bills = Bill.objects.all()[0:10]
    bills = [Bill.objects.get(pk=8581)]
    print(f'Got {len(bills)} bills.')

    for bill in bills:
        print(f'Processing {bill.id}')
        print(bill.text)
        # Fit model on data
        topics, _ = trained_model.transform(bill.text)

        if len(topics) == 0:
            print(f'No topics found for {bill.id}!!!')
            continue

        # Print the most frequent topics
        # top_topics = trained_model.get_topic_freq().head()

        # Print the most representative topic words
        topic_repr = trained_model.get_topic(topics[0])
        print(topic_repr[:10])

        if len(topics) > 1:
            # Determine similarity between top topic and other top 10 topics
            for topic in topics[1:]:
                similarity = get_similarity(trained_model, topics[0], topic)
                print(topic_repr[:3], '->', trained_model.get_topic(topic)[:3], similarity)
        else:
            print(f'Not enough topics found to do consistency check for {bill.id}!')
