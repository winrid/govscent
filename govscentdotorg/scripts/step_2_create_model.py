import logging
from os import path

import gensim


def run(wiki_path: str):
    logging.basicConfig(format='%(asctime)s : %(levelname)s : %(message)s', level=logging.INFO)
    print('Dictionary.load_from_text...')
    id2word = gensim.corpora.Dictionary.load_from_text(path.join(wiki_path, 'results_wordids.txt.bz2'))
    print('Loading corpus...')
    mm = gensim.corpora.MmCorpus(path.join(wiki_path, 'results_tfidf.mm'))
    print('Corpus details:', mm)
    print('Calculating model...')
    lda = gensim.models.ldamodel.LdaModel(corpus=mm, id2word=id2word, num_topics=2000, update_every=1, passes=10)
    print('Got topics:')
    lda.print_topics(100)
    print('Saving...')
    lda.save(path.join(wiki_path, 'ldamodelv1'))
    print('Saved!')
