#!/usr/bin/env python
# coding: utf-8

# Author: Vladimir M. Zaytsev <zaytsev@usc.edu>

import os
import numpy
import logging

from sear.utils import IndexerUtil
from sear.index import InvertedIndex

from sear.storage import LdbStorage
from sear.lexicon import DictLexicon

from metaphor.processing import LFSentenceParser
from metaphor.processing import LFSentenceStream
from metaphor.processing import LFSentenceIndexer


logging.basicConfig(level=logging.INFO)

input_fl = "/Users/zvm/code/isi/test_data/ruwac.part.817.malt.txt.lf"
test_out = "/Users/zvm/Desktop/tests"
lexicon_dir = "/Users/zvm/Desktop/tests/dlex.ldb"


logging.info("Initializing lexicon.")
lexicon = DictLexicon()
lexicon.read(lexicon_dir)


storage = LdbStorage(test_out)
index = InvertedIndex(test_out, [
    ("sent_id", numpy.int32),
])

# Initialize persistent storage backend.
logging.info("Initializing storage.")
storage.init_db()
storage.open_db()

logging.info("Initializing index.")
index.init_index()
index.open()


logging.info("Initializing lfs stream and indexer.")
sentence_stream = LFSentenceStream(input_fl)
sentence_parser = LFSentenceParser()
sentence_parser.init_id_counter(storage.documents_number)

sentence_indexer = LFSentenceIndexer(lexicon)
index_util = IndexerUtil(lexicon, index, storage)

logging.info("Start indexing file: %s" % input_fl)
logging.info("Input data size: %.2fMB" % (float(os.path.getsize(input_fl)) / (1024 ** 2)))
index_util.index_stream(sentence_stream, sentence_parser, sentence_indexer)

logging.info("Closing index.")
index.close()

logging.info("Closing storage.")
storage.close_db()

logging.info("Saving lexicon.")
lexicon.write(lexicon_dir)

logging.info("Oh my God, it's done!")