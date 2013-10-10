#!/usr/bin/env python
# coding: utf-8

# Author: Vladimir M. Zaytsev <zaytsev@usc.edu>

import os
import logging
import argparse
import collections

from sear.lexicon import DictLexicon                # Term lexicon backend.


logging.basicConfig(level=logging.INFO)


arg_parser = argparse.ArgumentParser()
arg_parser.add_argument("-s", "--test_size", type=str, choices=("tiny", "medium", "large"), default="tiny")
arguments = arg_parser.parse_args()


test_output = "test_out/%s/%s" % (arguments.test_size, "sentence")
if not os.path.exists(test_output):
    logging.error("Index directory does not exist: %s" % test_output)
    exit(0)


logging.info("Initializing lexicon.")
lexicon = DictLexicon(test_output)
lexicon.load()

counter = collections.Counter()
for term, term_id_and_freq in lexicon.term_dict.iteritems():
    counter[term] = term_id_and_freq[1]


for term, freq in counter.most_common():
    print "%d,%s" % (freq, term)