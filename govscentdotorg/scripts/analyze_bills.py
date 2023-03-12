# 3.

import re
import nltk
import gensim
from gensim.models.ldamulticore import LdaMulticore
from gensim import corpora, models
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from nltk.stem import WordNetLemmatizer
from sklearn.datasets import fetch_20newsgroups

from govscentdotorg.models import Bill

lemmatizer = WordNetLemmatizer()


def download_dependencies_get_stop_words() -> set[str]:
    nltk.download('wordnet')
    nltk.download('stopwords')
    nltk.download('punkt')
    return set(stopwords.words("english"))


def clean_text(text: str, stop_words: set[str]) -> str:
    # Text Cleaning (Removing Punctuations, Stopwords, Tokenization and Lemmatization)
    text = str(text).lower()
    text = re.sub(r'[^\w ]+', "", text)
    text = " ".join([lemmatizer.lemmatize(word, pos='v') for word in word_tokenize(text) if len(word) > 3 and word not in stop_words])

    return text


def make_biagram(data: [str], tokens: [str]):
    bigram = gensim.models.Phrases(data, min_count=5, threshold=100) # higher threshold fewer phrases.
    bigram_mod = gensim.models.phrases.Phraser(bigram)
    return [bigram_mod[doc] for doc in tokens]

def topic_modeling(data: [str]):
    # Tokens
    tokens = []
    for text in data:
        text_tokens = word_tokenize(text)
        tokens.append(text_tokens)

    # Make Biagrams
    tokens = make_biagram(data=data, tokens=tokens)

    # Corpora Dictionary
    dictionary = corpora.Dictionary(tokens)

    # Creating Document Term Matrix
    doc_term_matrix = [dictionary.doc2bow(doc) for doc in tokens]

    # Training The LDA Model
    lda_model = gensim.models.LdaModel(doc_term_matrix,   # Document Term Matrix
                                       num_topics = 100,     # Number of Topics
                                       id2word = dictionary,     # Word and Frequency Dictionary
                                       passes = 10,        # Number of passes throw the corpus during training (similar to epochs in neural networks)
                                       chunksize=10,       # Number of documents to be used in each training chunk
                                       update_every=1,     # Number of documents to be iterated through for each update.
                                       alpha='auto',       # number of expected topics that expresses
                                       per_word_topics=True,
                                       random_state=42)

    # Exploring Common Words For Each Topic With Their Relative Words
    for idx, topic in lda_model.print_topics():
        print("Topic: {} \nWords: {}".format(idx, topic ))
        print("\n")

    testing_bill = Bill.objects.get(pk=72770)
    bow = dictionary.doc2bow([clean_text([testing_bill.text])[0]])
    document_topics = lda_model.get_document_topics(bow)
    # print(document_topics)
    for topic, relevance in document_topics:
        print('----------------------------------')
        print(topic)
        print(relevance)
        print(lda_model.print_topic(topic))

def get_training_docs():
    return clean_text(fetch_20newsgroups(subset='all')['data'])
    # Yes, this means all the bill text needs to fit in memory. It takes around 1.5gb per 50k bills just for the text.
    # bills = Bill.objects.all().only("text")[:5000]
    # print(f'Training with {len(bills)} bills.')
    # bill_texts = []
    # for bill in bills:
    #     bill_texts.append(bill.text)
    # return clean_text(bill_texts)

def run():
    stop_words = download_dependencies_get_stop_words()
    print("Getting training data...")
    training_data = get_training_docs()
    print("Got training data...")
    topic_modeling(training_data)
