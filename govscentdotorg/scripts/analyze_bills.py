# 1. Use an existing model, since we want to determine topic similarity and our bills' content might throw this off...
# 2. Once we have topics and a way to calculate distance, we can parse our documents and use BERT's find_topics and find min/max/avg topic distance.
# 3. Topic distances, and distance from bill label, can be used to determine smelliness.

from bertopic import BERTopic
from bertopic.representation import TextGeneration

def get_similarity(model, topic_id_1: int, topic_id_2: int) -> float:
    """Calculate the similarity between two topics.

    Parameters
    ----------
    topic_id_1 : int
        The ID of the first topic.
    topic_id_2 : int
        The ID of the second topic.

    Returns
    -------
    float
        A similarity score between 0 and 1, where 0 is completely dissimilar and 1 is identical.
    """
    if topic_id_1 >= len(model.topic_embeddings) or topic_id_2 >= len(model.topic_embeddings):
        raise ValueError(f"Topics with IDs {topic_id_1} and/or {topic_id_2} do not exist.")
    topic_embedding_1 = model.topic_embeddings[topic_id_1]
    topic_embedding_2 = model.topic_embeddings[topic_id_2]
    return model.cosine_similarity([topic_embedding_1], [topic_embedding_2])[0][0]

def describe_topic():
    prompt = "I have a topic described by the following keywords: [KEYWORDS]. Based on the previous keywords, what is this topic about?"

    # Create your representation model
    generator = pipeline('text2text-generation', model='google/flan-t5-base')
    representation_model = TextGeneration(generator, prompt)
    print(representation_model.extract_topics())

# Load data
# data = pd.read_csv("news_articles.csv")

# Instantiate BERTopic with default parameters
model = BERTopic()

# Fit model on data
topics, _ = model.fit_transform(bill_text)

# Print the most frequent topics
print(model.get_topic_freq().head())

# Print the most representative topic words
topics_repr = model.get_topic(0)
print(topics_repr[:10])

# Determine similarity between two topics
similarity = get_similarity(model, 0, 1)
print(similarity)

