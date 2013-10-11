#!/usr/bin/env python
# coding: utf-8

# Author: Vladimir M. Zaytsev <zaytsev@usc.edu>

import os
import sys
import logging
import argparse
import collections

from sear.lexicon import DictLexicon


logging.basicConfig(level=logging.INFO)


arg_parser = argparse.ArgumentParser()
arg_parser.add_argument("-t", "--test", type=int, choices=(0, 1), default=0)
arg_parser.add_argument("-s", "--test_size", type=str, choices=("tiny", "medium", "large"), default="tiny")
arg_parser.add_argument("-i", "--input", type=str)
arguments = arg_parser.parse_args()


if arguments.test == 1:

    input_path = os.path.join(
        arguments.input,
        "test_out",
        arguments.test_size,
        "sentence"
    )

else:

    input_path = arguments.input


logging.info("Input: %s" % input_path)


logging.info("Initializing lexicon.")
lexicon = DictLexicon(input_path)
lexicon.load()


counter = collections.Counter()
for term, term_id_and_freq in lexicon.term_dict.iteritems():
    counter[term] = term_id_and_freq[1]

i = 0
sys.stdout.write("i,term,freq\n")
for term, freq in counter.most_common():
    i += 1
    sys.stdout.write("%d,%s,%d\n" % (i, term, freq))

logging.info("[DONE]")