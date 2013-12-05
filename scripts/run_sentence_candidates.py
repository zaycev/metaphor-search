#!/usr/bin/env python
# coding: utf-8

# Author: Vladimir M. Zaytsev <zaytsev@usc.edu>

import os
import re
import sys
import json
import glob
import nltk
import logging
import hashlib
import argparse

from sear.searcher import Searcher
from sear.storage import LdbStorage
from sear.index import InvertedIndex
from sear.lexicon import DictLexicon
from hugin.metaphor import find_path
from metaphor.ruwac import RuwacDocument
from metaphor.gigaword import text_to_terms


Q_TERM_RE = re.compile("(.+)\-([a-z]+)")
SENT_TOKENIZER = nltk.data.load('tokenizers/punkt/english.pickle')

logging.basicConfig(level=logging.INFO)

arg_parser = argparse.ArgumentParser()
arg_parser.add_argument("-i", "--input",            type=str)
arg_parser.add_argument("-c", "--context_input",    type=str, default=None)
arg_parser.add_argument("-l", "--language",         type=str, default=None)
arg_parser.add_argument("-f", "--output_format",    type=str, choices=("plain", "json"), default="plain")
arg_parser.add_argument("-o", "--output",           type=str, default=None)
arg_parser.add_argument("-x", "--put_lf",           type=int, default=0, choices=(0, 1))
arg_parser.add_argument("-q", "--query",            type=str)
arg_parser.add_argument("-e", "--extension",        type=str, default=".metaphors.json")
arg_parser.add_argument("-p", "--use_pos",          type=int, default=0, choices=(0, 1))
arg_parser.add_argument("-t", "--test",             type=int, choices=(0, 1), default=0)
arg_parser.add_argument("-s", "--test_size",        type=str, choices=("tiny", "medium", "large"), default="tiny")
arguments = arg_parser.parse_args()



def get_term_from_query(term_str, use_pos=False):
    if not use_pos:
        return term_str.encode("utf-8"), None
    else:
        term_matches = Q_TERM_RE.findall(term_str)
        if len(term_matches) != 1 or len(term_matches[0]) != 2:
            logging.warn("POS not found in term str: %s. Omitting POS." % term_str)
            return term_str, None
        else:
            return term_matches[0]


if arguments.test == 1:
    input_path = os.path.join(
        arguments.input,
        "test_out",
        arguments.test_size,
        arguments.language,
        "sentence"
    )
    query_paths = os.path.join(
        arguments.input,
        "test_data",
        arguments.test_size,
        arguments.language,
        "queries/*.json",
    )
    output_path = os.path.join(
        arguments.output,
        "test_out",
        arguments.test_size,
        arguments.language
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
    query_paths = arguments.query
    context_input = arguments.context_input

logging.info("Input: %s" % input_path)
logging.info("Context: %s" % context_input)
logging.info("Query: %s" % query_paths)
logging.info("Output: %s" % output_path)


logging.info("Initializing lexicon.")
lexicon = DictLexicon(input_path)
lexicon.load()


logging.info("Opening index.")
index = InvertedIndex(input_path)
index.open()


logging.info("Initializing searcher.")
searcher = Searcher(index, "sentence_id")

logging.info("Initializing storage.")
storage = LdbStorage(input_path)
storage.open_db()

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

for query_path in glob.glob(query_paths):

    if output_path is None:
        o_file = sys.stdout
    else:
        base_path = os.path.basename(query_path)
        o_file = open(os.path.join(output_path, base_path + arguments.extension), "wb")
    logging.info("Output file: %s" % o_file)

    # Get query parameters

    logging.info("Reading query: %s" % query_path)

    q_json = json.load(open(query_path, "rb"))

    q_label = q_json.get("annotation", dict()).get("label")
    q_corpus = q_json.get("annotation", dict()).get("corpus")
    q_targets = q_json.get("query", dict()).get("targets")
    q_sources = q_json.get("query", dict()).get("sources")
    q_max_path_length = q_json.get("query", dict()).get("max_path_length", 0)
    q_source_frame = q_json.get("annotation", dict()).get("source_frame", None)
    q_source_concept_subdomain = q_json.get("annotation", dict()).get("source_concept_subdomain", None)
    q_target_frame = q_json.get("annotation").get("target_frame", None)
    q_target_concept_domain = q_json.get("annotation").get("target_concept_domain", None)
    q_target_concept_subdomain = q_json.get("annotation").get("target_concept_subdomain", None)
    q_language = q_json.get("annotation", dict()).get("language")

    mini_dict = dict()

    targets = []
    for term_str in q_targets:
        term, pos = get_term_from_query(term_str, arguments.use_pos == 1)
        term_id = lexicon.get_id(term)
        if term_id != -1:
            mini_dict[term_id] = (term, pos)
            targets.append(term_id)
        else:
            logging.error("Target term not found in dictionary: %s" % term)

    sources = []
    for term_str in q_sources:
        term, pos = get_term_from_query(term_str, arguments.use_pos == 1)
        term_id = lexicon.get_id(term)
        if term_id != -1:
            mini_dict[term_id] = (term, pos)
            sources.append(term_id)
        else:
            logging.error("Source term not found in dictionary: %s" % term)

    # Encode query, e.g. get ID of each term
    logging.info("Encoding query.")

    targets = [(term_id, []) for term_id in targets]
    sources = [(term_id, []) for term_id in sources]
    logging.info("Query has %d x %d terms" % (len(targets), len(sources)))


    # This tables will contain : document_id -> <sources, targets>
    candidates = dict()
    target_candidates = searcher.find_or(targets)
    source_candidates = searcher.find_or(sources)

    # For every source document, check if it also has targets, then remeber its sources, otherwise
    # remove that document from the hashmap
    for document_id, found_sources in source_candidates.iteritems():
        if document_id in target_candidates:
            found_targets = target_candidates[document_id]
            candidates[document_id] = [found_sources, found_targets]

    logging.info("Found target docs: %d" % len(target_candidates))
    logging.info("Found source docs: %d" % len(source_candidates))
    logging.info("After intersection: %d" % len(candidates))


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
        sent_hash = str(hashlib.md5(sent_text).hexdigest())

        if arguments.language == "ru":
            sent_terms = [term.encode("utf-8") for term in sent_document["t"]]
        else:
            sent_text_u = sent_text.decode("utf-8")
            sent_terms = [t for t in text_to_terms(sent_text_u, arguments.language)]

        if sent_hash in sent_hashes:
            logging.info("Skipped sentence, because we've seen its hash before: %s" % sent_hash[:8])
            continue
        else:
            logging.info("Added a new sentence digest to the duplicates hash set: %s" %  sent_hash[:8])
            sent_hashes.add(sent_hash)

        try:
            for target_term_id in targets:
                for source_term_id in sources:

                    if target_term_id == source_term_id:
                        logging.warn("Got equal target and source in %r" % query_path)
                        continue

                    source_term, source_pos = mini_dict[source_term_id]
                    target_term, target_pos = mini_dict[target_term_id]
                    source_p, target_p, found = find_path(target_term,
                                                          source_term,
                                                          target_pos,
                                                          source_pos,
                                                          sent_lf_text,
                                                          use_pos=arguments.use_pos == 1,
                                                          max_path_length=q_max_path_length,
                                                          language=arguments.language)
                    if not found:
                        logging.info("Path not found in %s" % sent_hash[:8])

                    if found:

                        if arguments.output_format == "plain":
                            sys.stdout.write("[source:%s, target:%s]\n%s\n%s\n\n" % (
                                source_term,
                                target_term,
                                sent_text,
                                sent_lf_text,
                            ))

                        elif arguments.output_format == "json":

                            sentence_list = []
                            if context_input is not None:

                                c_query = [(c_lexicon.get_id(term), [])
                                           for term in sent_terms
                                           if c_lexicon.get_id(term) != -1]

                                logging.info("Searching context using %d of %d terms" % (len(c_query), len(sent_terms)))
                                c_candidates = found_contexts = c_searcher.find(c_query)
                                logging.info("Found %d candidates for context", len(c_candidates))

                                for doc_id in c_candidates:
                                    document_blob = c_storage.get_document(doc_id)
                                    document = RuwacDocument(doc_id)
                                    document.fromstring(document_blob)

                                    if arguments.language == "ru":
                                        document_terms = [term.encode("utf-8")
                                                          for sent in document.content
                                                          for term in sent]
                                        document_text = " ".join(document_terms)
                                    elif arguments.language == "es" or arguments.language == "en":
                                        document_text = document.content
                                    else:
                                        raise Exception("Unsupported language.")

                                    if sent_text in document_text:

                                        if arguments.language == "ru":
                                            sentence_list = [" ".join(sent).encode("utf-8") for sent in document.content]
                                        elif arguments.language == "es" or arguments.language == "en":
                                            sentence_list = SENT_TOKENIZER.tokenize(document_text)
                                        else:
                                            raise Exception("Unsupported language.")

                                        logging.info("Found at least one matching document.")
                                        break

                            if target_p.term_id < source_p.term_id:
                                a, b = target_p.term_id, source_p.term_id
                            elif target_p.term_id > source_p.term_id:
                                a, b = source_p.term_id, target_p.term_id
                            else:
                                a, b = source_p.term_id, target_p.term_id
                                logging.error("Error occurred, target id == source id")

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
                                        "source": source_term,
                                        "targetInLm": True,
                                        "target": target_term,
                                    },
                                    "sourceFrame": q_source_frame,
                                    "sourceConceptSubDomain": q_source_concept_subdomain,
                                    "targetFrame": q_target_frame,
                                    "targetConceptDomain": q_target_concept_domain,
                                    "targetConceptSubDomain": q_target_concept_subdomain
                                },
                                "language": q_language,
                                "sentenceList": sentence_list,
                                "url": "",
                            }

                            if arguments.put_lf:
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

    o_file.close()
