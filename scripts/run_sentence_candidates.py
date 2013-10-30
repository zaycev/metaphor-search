#!/usr/bin/env python
# coding: utf-8

# Author: Vladimir M. Zaytsev <zaytsev@usc.edu>

import os
import gc
import sys
import json
import logging
import argparse
import hashlib

from sear.searcher import Searcher
from sear.storage import LdbStorage
from sear.index import InvertedIndex
from sear.lexicon import DictLexicon

from hugin.metaphor import find_path

from metaphor.ruwac import RuwacDocument


logging.basicConfig(level=logging.INFO)

arg_parser = argparse.ArgumentParser()
arg_parser.add_argument("-t", "--test",             type=int, choices=(0, 1), default=0)
arg_parser.add_argument("-s", "--test_size",        type=str, choices=("tiny", "medium", "large"), default="tiny")
arg_parser.add_argument("-l", "--language",         type=str, default=None)
arg_parser.add_argument("-f", "--output_format",    type=str, choices=("plain", "json"), default="plain")
arg_parser.add_argument("-q", "--query_file",       type=str)
arg_parser.add_argument("-i", "--input",            type=str)
arg_parser.add_argument("-c", "--context_input",    type=str, default=None)
arg_parser.add_argument("-o", "--output",           type=str, default=None)
arg_parser.add_argument("-g", "--output_lf",        type=int, default=0, choices=(0, 1))
arguments = arg_parser.parse_args()


if arguments.test == 1:
    input_path = os.path.join(
        arguments.input,
        "test_out",
        arguments.test_size,
        arguments.language,
        "sentence"
    )
    query_path = os.path.join(
        arguments.input,
        "test_data",
        arguments.test_size,
        arguments.language,
        "query.json",
    )
    output_path = os.path.join(
        arguments.output,
        "test_out",
        arguments.test_size,
        arguments.language,
        "candidates.json"
    )
    context_input = os.path.join(
        arguments.output,
        "test_out",
        arguments.test_size,
        arguments.language,
        "document"
    )
else:
    input_path = arguments.input
    output_path = arguments.output
    query_path = arguments.query_file
    context_input = arguments.context_input


logging.info("Input: %s" % input_path)
logging.info("Context: %s" % context_input)
logging.info("Query: %s" % query_path)
logging.info("Output: %s" % output_path)

if output_path is None:
    o_file = sys.stdout
else:
    o_file = open(output_path, "wb")


logging.info("Initializing lexicon.")
lexicon = DictLexicon(input_path)
lexicon.load()


logging.info("Opening index.")
index = InvertedIndex(input_path)
index.open()


logging.info("Initializing searcher.")
searcher = Searcher(index, "sentence_id")

if context_input is not None:

    logging.info("Initializing context lexicon.")
    c_lexicon = DictLexicon(context_input)
    c_lexicon.load()


    logging.info("Opening context index.")
    c_index = InvertedIndex(context_input)
    c_index.open()

    logging.info("Initializing context searcher.")
    if arguments.language == "ru":
        c_searcher = Searcher(c_index, "ruwac_document_id")
    else:
        c_searcher = Searcher(c_index, "document_id")

    logging.info("Initializing context storage.")
    c_storage = LdbStorage(context_input)
    c_storage.open_db()



logging.info("Reading query.")
j_query = json.load(open(query_path, "rb"))
q_label = j_query.get("annotation", dict()).get("label")
q_corpus = j_query.get("annotation", dict()).get("corpus")
q_targets = j_query.get("query", dict()).get("targets")
q_sources = j_query.get("query", dict()).get("sources")
q_max_path_length =  j_query.get("query", dict()).get("max_path_lenght", 0)

q_source_frame = j_query.get("annotation", dict()).get("source_frame", None)
q_source_concept_subdomain = j_query.get("annotation", dict()).get("source_concept_subdomain", None)

q_target_frame = j_query.get("annotation").get("target_frame", None)
q_target_concept_domain = j_query.get("annotation").get("target_concept_domain", None)
q_target_concept_subdomain = j_query.get("annotation").get("target_concept_subdomain", None)

q_language = j_query.get("annotation", dict()).get("language")

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

logging.info("Initializing context storage storage.")


logging.info("Checking candidates.")
proven = []
entries = []
sent_hashes = set()

if arguments.output_format == "json":
    o_file.write("[")

iter = 0

for sent_document_id, (sources, targets) in candidates.iteritems():
    sent_document = json.loads(storage.get_document(sent_document_id))


    sent_text = sent_document["r"].encode("utf-8")
    sent_lf_text = sent_document["s"].encode("utf-8")
    sent_terms = [term.encode("utf-8") for term in sent_document["t"]]
    sent_hash = str(hashlib.md5(sent_text).hexdigest())

    if sent_hash in sent_hashes:
        logging.info("Skipped sentence, because we've seen its hash before: %s" % sent_hash[:8])
        continue
    else:
        logging.info("Added a new sentence digest to the duplicates hash set: %s" %  sent_hash[:8])
        sent_hashes.add(sent_hash)

    try:
        for target_term_id in targets:
            for source_term_id in sources:

                source_term = mini_dict[source_term_id]
                target_term = mini_dict[target_term_id]
                source_p, target_p, found = find_path(target_term,
                                                      source_term,
                                                      sent_lf_text,
                                                      max_path_length=q_max_path_length)

                if found:

                    if arguments.output_format == "plain":
                        sys.stdout.write("[source:%s, target:%s]\n%s\n%s\n\n" % (
                            source_term,
                            target_term,
                            sent_text,
                            sent_lf_text,
                        ))

                    elif arguments.output_format == "json":
                        if context_input is not None:

                            c_query = [(c_lexicon.get_id(term), [])
                                        for term in sent_terms
                                        if c_lexicon.get_id(term) != -1]

                            logging.info("Searching context using %d of %d terms" % (len(c_query), len(sent_terms)))
                            c_candidates = found_contexts = c_searcher.find(c_query)
                            logging.info("Found %d candidates for context", len(c_candidates))

                            matched_context = []
                            matched_context_s = []
                            for doc_id in c_candidates:
                                document_blob = c_storage.get_document(doc_id)
                                document = RuwacDocument(doc_id)
                                document.fromstring(document_blob)
                                document_terms = [term.encode("utf-8") for sent in document.content for term in sent]
                                document_text = " ".join(document_terms)
                                if sent_text in document_text:
                                    sentence_list = [" ".join(sent) for sent in document.content]
                                    matched_context.append(document)
                                    matched_context_s.append(sentence_list)
                            logging.info("Found %d matching documents", len(matched_context))

                        else:

                            matched_context = []
                            matched_context_s = []



                        if target_p.term_id < source_p.term_id:
                            a, b = target_p.term_id, source_p.term_id
                        elif target_p.term_id > source_p.term_id:
                            a, b = source_p.term_id, target_p.term_id
                        else:
                            a, b = source_p.term_id, target_p.term_id
                            logging.error("Error occured, target id == source id")

                        context = []
                        raw_sentence_terms = sent_text.split(" ")
                        for k, term in enumerate(raw_sentence_terms):
                            if k == a:
                                context.append("======> *")
                                context.append(term)
                            elif k == b:
                                context.append(term)
                                context.append("<====== *")
                            else:
                                context.append(term)

                        entry = {
                            "metaphorAnnotationRecords": {
                                "linguisticMetaphor": " ".join(raw_sentence_terms[a:(b + 1)]).decode("utf-8"),
                                "context": " ".join(context).decode("utf-8"),
                                "annotationMappings": {
                                    "sourceInLm": True,
                                    "source": source_term.decode("utf-8"),
                                    "targetInLm": True,
                                    "target": target_term.decode("utf-8")
                                },
                                "sourceFrame": q_source_frame,
                                "sourceConceptSubDomain": q_source_concept_subdomain,
                                "targetFrame": q_target_frame,
                                "targetConceptDomain": q_target_concept_domain,
                                "targetConceptSubDomain": q_target_concept_subdomain
                            },
                            "language": q_language,
                            "sentenceList": [] if len(matched_context) == 0 else matched_context_s[0],
                            "url": "" if len(matched_context) == 0 else matched_context[0].url,
                        }

                        if arguments.output_lf:
                            entry["logic_form"] = sent_lf_text.decode("utf-8")

                        entries.append(entry)
                        if iter != 0:
                            o_file.write(",\n")
                        o_file.write(json.dumps(entry, indent=8, ensure_ascii=False).encode("utf-8"))
                        iter += 1

    except Exception:
        import traceback
        logging.error(traceback.format_exc())
        logging.error("Exiting")


if arguments.output_format == "json":
    o_file.write("\n]")
