#!/usr/bin/env python
# coding: utf-8

# Author: Vladimir M. Zaytsev <zaytsev@usc.edu>

import os
import sys
import numpy
import logging


from sear.searcher import Searcher
from sear.storage import LdbStorage
from sear.index import InvertedIndex
from sear.lexicon import DictLexicon

from metaphor.processing import RuwacDocument

logging.basicConfig(level=logging.INFO)

test_out = "/Users/zvm/Desktop/tests"
lexicon_dir = "/Users/zvm/Desktop/tests/dlex.ldb"


logging.info("Initializing lexicon.")
lexicon = DictLexicon()
lexicon.load(lexicon_dir)

index = InvertedIndex(test_out)
index.open()
index.load_to_memory()

searcher = Searcher(index)

term_id_1 = lexicon.get_id(u"президент".encode("utf-8"))
term_id_2 = lexicon.get_id(u"дмитрий".encode("utf-8"))

ids = searcher.find(query=[
		(term_id_1, []), # AND
	], ret_field="rdoc_id")

storage = LdbStorage(test_out)
storage.open_db()

for doc_id in ids:
	raw_doc = storage.get_document(str(doc_id))
	document = RuwacDocument(doc_id, None, None, None, None)
	document.fromstring(raw_doc)
	for sent in document.content:
		for term in sent:
			print term.encode("utf-8")