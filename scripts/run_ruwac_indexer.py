#!/usr/bin/env python
# coding: utf-8

# Author: Vladimir M. Zaytsev <zaytsev@usc.edu>

import os
import sys
import numpy
import logging


from sear.utils import IndexerUtil
from sear.index import InvertedIndex

from sear.storage import LdbStorage
from sear.lexicon import DictLexicon
from sear.lexicon import DATrieLexicon

from metaphor.processing import RuwacParser
from metaphor.processing import RuwacStream
from metaphor.processing import RuwacIndexer

logging.basicConfig(level=logging.INFO)

input_fl = "/Users/zvm/code/isi/metaphor/test_data/ruwac_1M.txt"
test_out = "/Users/zvm/Desktop/tests"
alphabet_fl = "/Users/zvm/Desktop/tests/alphabet.txt"
lexicon_dir = "/Users/zvm/Desktop/tests/dlex.ldb"

# alphabet = collect_alphabet(input_fl, TripletParser(), alphabet_fl)
# logging.info("Using alphabet: %s" % alphabet_fl)
# logging.info("Alphabet size: %d ch" % len(alphabet))

logging.info("Initializing lexicon.")
lexicon = DictLexicon()
lexicon.read(lexicon_dir)


storage = LdbStorage(test_out)
index = InvertedIndex(test_out, [
    ("rdoc_id", numpy.int32),
])

# Initialize persistent storage backend.
logging.info("Initializing storage.")
storage.init_db()
storage.open_db()

logging.info("Initializing index.")
index.init_index()
index.open()


logging.info("Initializing ruwac stream and indexer.")
ruwac_stream = RuwacStream.open(input_fl)
ruwac_parser = RuwacParser()
ruwac_parser.init_id_counter(storage.documents_number)

ruwac_indexer = RuwacIndexer(lexicon)
index_util = IndexerUtil(lexicon, index, storage)

logging.info("Start indexing file: %s" % input_fl)
logging.info("Input data size: %.2fMB" % (float(os.path.getsize(input_fl)) / (1024 ** 2)))
index_util.index_stream(ruwac_stream, ruwac_parser, ruwac_indexer)

logging.info("Closing index.")
index.close()

logging.info("Closing storage.")
storage.close_db()

logging.info("Saving lexicon.")
lexicon.write(lexicon_dir)

logging.info("Oh my God, it's done!")