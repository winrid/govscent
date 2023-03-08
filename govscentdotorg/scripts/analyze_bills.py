# 1. Ideally we use an existing model, since we want to determine topic similarity and our bills' content might throw this off...
#   However, we are having trouble getting more than 0/1 topics from a bill with BERT using the newsgroups model, so for now we are trained off the bills themselves...
# 2. Once we have topics and a way to calculate distance, we can parse our documents and use BERT's find_topics and find min/max/avg topic distance.
# 3. Topic distances, and distance from bill label, can be used to determine smelliness.
import re
import nltk
import gensim
from gensim.models.ldamulticore import LdaMulticore
from gensim import corpora, models
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from nltk.stem import WordNetLemmatizer

from govscentdotorg.models import Bill

lemmatizer = WordNetLemmatizer()

def clean_text(lst):
    cleaned_text = []
    stopwords_set = set(stopwords.words("english"))

    # Text Cleaning (Removing Punctuations, Stopwords, Tokenization and Lemmatization)
    for text in lst:
        text = str(text).lower()
        text = re.sub(r'[^\w ]+', "", text)
        text = " ".join([lemmatizer.lemmatize(word,pos='v') for word in word_tokenize(text) if len(word) > 3 and word not in stopwords_set])
        cleaned_text.append(text)

    return cleaned_text


def make_biagram(data: [str], tokens: [str]):
    bigram = gensim.models.Phrases(data, min_count=5, threshold=100) # higher threshold fewer phrases.
    bigram_mod = gensim.models.phrases.Phraser(bigram)
    return [bigram_mod[doc] for doc in tokens]

def topic_modeling(data: [str]):
    nltk.download('punkt')
    print('Punkt downloaded.')
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
    bow = dictionary.doc2bow([testing_bill.text])
    document_topics = lda_model.get_document_topics(bow)
    # print(document_topics)
    for topic, relevance in document_topics:
        print(topic)
        print(relevance)
        print('----')
        print(lda_model.print_topic(topic))

def get_training_docs():
    # return fetch_20newsgroups(subset='all')['data']
    # Yes, this means all the bill text needs to fit in memory. It takes around 1.5gb per 50k bills just for the text.
    bills = Bill.objects.all().only("text")[:50]
    print(f'Training with {len(bills)} bills.')
    bill_texts = []
    for bill in bills:
        bill_texts.append(bill.text)
    return bill_texts

def run():
    print("Getting training data...")
    training_data = get_training_docs()
    print("Got training data...")
    topic_modeling(training_data)
