#!/usr/bin/env python
# coding: utf-8

# Author: Vladimir M. Zaytsev <zaytsev@usc.edu>

import os
import gc
import sys
import json
import random
import logging
import argparse

from sear.searcher import Searcher
from sear.storage import LdbStorage
from sear.index import InvertedIndex
from sear.lexicon import DictLexicon

from hugin.metaphor import find_path


logging.basicConfig(level=logging.INFO)

arg_parser = argparse.ArgumentParser()
arg_parser.add_argument("-t", "--test", type=int, choices=(0, 1), default=0)
arg_parser.add_argument("-s", "--test_size", type=str, choices=("tiny", "medium", "large"), default="tiny")
arg_parser.add_argument("-l", "--test_language", type=str, choices=("russian",), default="russian")
arg_parser.add_argument("-f", "--output_format", type=str, choices=("plain", "json", "pkl",), default="plain")
arg_parser.add_argument("-q", "--query_file", type=str)
arg_parser.add_argument("-i", "--input", type=str)
arg_parser.add_argument("-o", "--output", type=str)
arguments = arg_parser.parse_args()


if arguments.test == 1:
    input_path = os.path.join(
        arguments.input,
        "test_out",
        arguments.test_size,
        "sentence"
    )
    query_path = os.path.join(
        arguments.input,
        "test_data",
        arguments.test_size,
        "%s.json" % arguments.test_language
    )
    output_path = os.path.join(
        arguments.output,
        "test_out",
        arguments.test_size,
        "%s.txt" % arguments.test_language
    )
else:
    input_path = arguments.input
    output_path = arguments.output
    query_path = arguments.query_file


logging.info("Input: %s" % input_path)
logging.info("Query: %s" % query_path)
logging.info("Output: %s" % output_path)


logging.info("Initializing lexicon.")
lexicon = DictLexicon(input_path)
lexicon.load()


logging.info("Opening index.")
index = InvertedIndex(input_path)
index.open()


logging.info("Initializing searcher.")
searcher = Searcher(index, "sentence_id")


logging.info("Reading query.")
j_query = json.load(open(query_path, "rb"))
q_label = j_query.get("annotation", dict()).get("label")
q_language = j_query.get("annotation", dict()).get("language")
q_corpus = j_query.get("annotation", dict()).get("corpus")
q_targets = j_query.get("query", dict()).get("targets")
q_sources = j_query.get("query", dict()).get("sources")

mini_dict = dict()
for term in q_targets:
    term_id = lexicon.get_id(term.encode("utf-8"))
    if term_id != -1:
        mini_dict[term_id] = term.encode("utf-8")
for term in q_sources:
    term_id = lexicon.get_id(term.encode("utf-8"))
    if term_id != -1:
        mini_dict[term_id] = term.encode("utf-8")

# Encode query, e.g. get ID of each term
logging.info("Encoding query.")
targets = [lexicon.get_id(term.encode("utf-8")) for term in q_targets]
sources = [lexicon.get_id(term.encode("utf-8")) for term in q_sources]

targets = [(term_id, []) for term_id in targets if term_id != -1]
sources = [(term_id, []) for term_id in sources if term_id != -1]

s_targets = [(term_id, []) for term_id in targets if term_id == -1]
s_sources = [(term_id, []) for term_id in sources if term_id == -1]

logging.info("Query has %d x %d terms" % (len(targets), len(sources)))
if len(s_sources) + len(s_sources) == 0:
    logging.info("No terms were skipped")
else:
    logging.info("%d x %d terms were skipped" % (len(s_targets), len(s_sources)))


candidates = dict()
target_candidates = searcher.find_or(targets)
source_candidates = searcher.find_or(sources)

# For every source document, check if it also has targets, then remeber its sources, otherwise
# remove that document from the hashmap
for document_id, found_sources in source_candidates.iteritems():
    if document_id in target_candidates:
        candidates[document_id] = [found_sources, target_candidates[document_id]]

logging.info("Found target docs: %d" % len(target_candidates))
logging.info("Found source docs: %d" % len(source_candidates))
logging.info("After intersection: %d" % len(candidates))


logging.info("Releasing index and searcher.")
index = None
storage = None
gc.collect()

logging.info("Initializing storage.")
storage = LdbStorage(input_path)
storage.open_db()


logging.info("Checking candidates.")
proven = []
for document_id, (sources, targets) in candidates.iteritems():
    document = storage.get_document(document_id)

    text = json.loads(document)["r"].encode("utf-8")
    lf_text = json.loads(document)["s"].encode("utf-8")

    for target_term_id in targets:
        for source_term_id in sources:
            target_term = mini_dict[target_term_id]
            source_term = mini_dict[source_term_id]
            found = find_path(target_term, source_term, lf_text)
            if found:
                if arguments.output_format == "plain":
                    sys.stdout.write("[source:%s, target:%s]\n%s\n%s\n\n" % (
                        source_term,
                        target_term,
                        text,
                        lf_text,
                    ))