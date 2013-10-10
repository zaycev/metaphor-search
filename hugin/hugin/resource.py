#!/usr/bin/env python
# coding: utf-8

# Copyright (C) USC Information Sciences Institute
# Author: Vladimir M. Zaytsev <zaytsev@usc.edu>
# URL: <http://nlg.isi.edu/>
# For more information, see README.md
# For license information, see LICENSE

import csv
import logging


class ConceptNetRelations(object):
    CRT = 0x00
    DRF = 0x01
    SYN = 0x02


class ConceptNetList(object):
    rel_id_map = {
        "ConceptuallyRelatedTo": ConceptNetRelations.CRT,
        "DerivedFrom": ConceptNetRelations.DRF,
        "Synonym": ConceptNetRelations.SYN
    }

    def __init__(self, relations, engine=None):
        self.relations = relations
        self.cnet_id_map = None
        if engine is not None:
            self.cnet_id_map = dict()
            mapped = 0
            for rel_type, arg1, arg2, pos in relations:
                arg_1_id = engine.term_id_map.get(arg1)
                arg_2_id = engine.term_id_map.get(arg2)
                if arg_1_id is not None and arg_2_id is not None:
                    mapped += 1
                    if arg_1_id in self.cnet_id_map:
                        self.cnet_id_map[arg_1_id].add(arg_2_id)
                    else:
                        self.cnet_id_map[arg_1_id] = {arg_2_id}
            logging.info("CREATED CONCEPT NET WITH %d RELATIONS" % mapped)

    def __contains__(self, item):
        if self.cnet_id_map is None:
            return None
        arg1, arg2 = item
        if arg1 in self.cnet_id_map and arg2 in self.cnet_id_map[arg1]:
            return True
        if arg2 in self.cnet_id_map and arg1 in self.cnet_id_map[arg2]:
            return True
        return False

    @staticmethod
    def load(file_path, rels=None, engine=None):
        relations = []
        with open(file_path, "rb") as fl:
            reader = csv.reader(fl, delimiter=";")
            for rel, arg1, arg2 in reader:
                arg_and_pos = arg2.split("/")
                if len(arg_and_pos) == 2:
                    arg2, pos = arg_and_pos
                else:
                    arg2, pos = arg_and_pos[0], None
                if rel == "ConceptuallyRelatedTo":
                    rel_short = "c"
                elif rel == "DerivedFrom":
                    rel_short = "d"
                elif rel == "Synonym":
                    rel_short = "s"
                else:
                    rel_short = None
                    print rel
                if rel_short in rels:
                    relations.append((ConceptNetList.rel_id_map[rel], arg1, arg2, pos))
        logging.info("LOADED %d %s CONCEPTS" % (len(relations), rels))
        return ConceptNetList(relations, engine)


class StopList(object):

    def __init__(self, stop_words, engine=None):
        self.stop_words = stop_words
        self.stop_words_ids = set()
        if engine is not None:
            for word in self.stop_words:
                term_id = engine.term_id_map.get(word)
                if term_id is not None:
                    self.stop_words_ids.add(term_id)

    @staticmethod
    def load(file_path, threshold=500.0, engine=None):
        stop_terms_set = set()
        try:
            with open(file_path, "rb") as csvfile:
                stop_terms = csv.reader(csvfile, delimiter=",")
                for rank, freq, lemma, pos in stop_terms:
                    freq = float(freq)
                    if freq >= threshold:
                        stop_terms_set.add(lemma)
                    else:
                        break
        except IOError:
            pass
        logging.info("LOADED %d (f<=%f) STOP WORDS" % (len(stop_terms_set), threshold))
        return StopList(stop_terms_set, engine)

    def __contains__(self, item):
        if isinstance(item, int):
            return item in self.stop_words_ids
        elif isinstance(item, basestring):
            return item in self.stop_words
        return False