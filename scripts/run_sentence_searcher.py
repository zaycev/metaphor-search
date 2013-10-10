#!/usr/bin/env python
# coding: utf-8

# Author: Vladimir M. Zaytsev <zaytsev@usc.edu>

import os
import random
import logging
import argparse

from sear.searcher import Searcher
from sear.index import InvertedIndex
from sear.lexicon import DictLexicon


logging.basicConfig(level=logging.INFO)

arg_parser = argparse.ArgumentParser()
arg_parser.add_argument("-t", "--test", type=int, choices=(0, 1), default=0)
arg_parser.add_argument("-s", "--test_size", type=str, choices=("tiny", "medium", "large"), default="tiny")
arg_parser.add_argument("-l", "--test_samples", type=int, default=512)
arg_parser.add_argument("-d", "--query_size", type=int, default=3)
arg_parser.add_argument("-i", "--input", type=str)
arg_parser.add_argument("-o", "--output", type=str)
arguments = arg_parser.parse_args()


logging.info("Initializing output directory structure.")

if arguments.test == 1:

    input_path = os.path.join(
        arguments.input,
        "test_data",
        arguments.test_size,
        "sentence"
    )
    output_path = os.path.join(
        arguments.output,
        "test_out",
        arguments.test_size,
        "sentence"
    )
else:

    input_path = arguments.input
    output_path = arguments.output

logging.info("Input: %s" % input_path)
logging.info("Output: %s" % output_path)

logging.info("Initializing lexicon.")
lexicon = DictLexicon(output_path)
lexicon.load()

logging.info("Opening index.")
index = InvertedIndex(output_path)
index.open()


if arguments.test == 1:
    all_terms = lexicon.term_dict.keys()
    logging.info("Generating %d x %d queries." % (arguments.test_samples, arguments.query_size))
    queries = []
    for i in xrange(arguments.test_samples):
        query = []
        for j in xrange(arguments.query_size):
            term = random.choice(all_terms)
            query.append((term, []))
        queries.append(query)


    searcher = Searcher(index)

    for query in queries:
        encoded_query = [(lexicon.get_id(t[0]), []) for t in query]
        candidates = searcher.find(encoded_query, "sentence_id")
        query_pretty = " ".join([t[0] for t in query])
        logging.debug("%d\tdocs found while processing query \"%s\"" % (
            len(candidates),
            query_pretty,
        ))
