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

from metaphor.processing import TripletParser
from metaphor.processing import TripletIndexer

from metaphor.alpcollect import collect_alphabet


logging.basicConfig(level=logging.INFO)

input_fl = "/Users/zvm/code/isi/metaphor/test_data/1M.csv"
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
    ("triple_id", numpy.int32),
    ("position", numpy.int8),
    ("relation", numpy.int8),
    ("freq", numpy.int32),
])

# Initialize persistent storage backend.
logging.info("Initializing storage.")
storage.init_db()
storage.open_db()

logging.info("Initializing index.")
index.init_index()
index.open()


logging.info("Initializing triplet stream and indexer.")
triplet_stream = open(input_fl, "rb")
triplet_parser = TripletParser()
triplet_parser.init_id_counter(storage.documents_number)

triplet_indexer = TripletIndexer(lexicon)
index_util = IndexerUtil(lexicon, index, storage)

logging.info("Start indexing file: %s" % input_fl)
logging.info("Input data size: %.2fMB" % (float(os.path.getsize(input_fl)) / (1024 ** 2)))
index_util.index_stream(triplet_stream, triplet_parser, triplet_indexer)

logging.info("Closing index.")
index.close()

logging.info("Closing storage.")
storage.close_db()

logging.info("Saving lexicon.")
lexicon.write(lexicon_dir)

logging.info("Oh my God, it's done!")
