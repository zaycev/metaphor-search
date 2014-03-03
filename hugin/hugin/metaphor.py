#!/usr/bin/env python
# coding: utf-8

# Copyright (C) USC Information Sciences Institute
# Author: Vladimir M. Zaytsev <zaytsev@usc.edu>
# URL: <http://nlg.isi.edu/>
# For more information, see README.md
# For license information, see LICENSE

import re
import logging

EN_TERM_RE = re.compile("(.+)(\-(.+))?")
SENT_RE = re.compile("((\[.+?\]\:)?([^ .]+?)(\-[a-z]+)?(\([,a-z0-9]+?\)))")
SENT_BOXER_RE = re.compile("((\[.*?\]\:)?([^ .]+?)(\-[a-z]+)?(\([,a-z0-9]+?\)))")


class Predicate(object):

    def __init__(self, p_id, lemma, pos, args, term_id):
        self.p_id = p_id
        self.lemma = lemma
        self.pos = pos
        self.args = args
        self.term_id = term_id

    def __repr__(self):
        return "<Predicate(%d, %s, %s, %s)>" % (
            self.p_id,
            self.lemma,
            (" " + self.pos) if self.pos else "",
            self.args,
        )


def find_path(source,
              target,
              source_pos,
              target_pos,
              sentence,
              use_pos=False,
              max_path_length=0,
              language=None):

    if language == "rus" or language == "spa":
        predicates = parse_sent(sentence)
    elif language == "eng":
        predicates = parse_boxer_sent(sentence)
    else:
        raise Exception("Unsupported language %s.\nLogic form: %s" % (
            language,
            sentence
        ))

    if use_pos:
        sources = [pred for pred in predicates if pred.lemma == source]
        targets = [pred for pred in predicates if pred.lemma == target]
    else:
        sources = [pred for pred in predicates
                   if pred.lemma == source and (pred.pos == source_pos or source_pos is None)]
        targets = [pred for pred in predicates
                   if pred.lemma == target and (pred.pos == target_pos or target_pos is None)]

    arg_predicates = dict()
    for pred in predicates:
        for arg in pred.args:
            if arg not in arg_predicates:
                arg_predicates[arg] = [pred]
            else:
                arg_predicates[arg].append(pred)
    for target in targets:
        for source in sources:
            found = __path_exists__(source, target, predicates, arg_predicates, max_path_length)
            if found:
                return source, target, True
    return None, None, False


def parse_sent(lf_text):
    matches = SENT_RE.findall(lf_text)
    predicates = []
    for i, match in enumerate(matches):
        term_id = match[1]
        term_id = match[1][(len(term_id)-5):(len(term_id)-2)]
        if term_id != "":
            term_id = int(term_id) - 1
        else:
            term_id = -1
        lemma = match[2]
        pos = match[3][1:]
        args = match[4][1:(len(match[4]) - 1)].split(",")
        predicates.append(Predicate(i, lemma, pos, args, term_id))

    return predicates


def parse_boxer_sent(lf_text):
    matches = SENT_BOXER_RE.findall(lf_text)
    predicates = []
    for i, match in enumerate(matches):
        term_id = match[1]
        term_id = match[1][(len(term_id)-5):(len(term_id)-2)]
        if term_id != "":
            term_id = int(term_id) - 1
        else:
            term_id = -1
        lemma = match[2]
        pos = match[3][1:]
        args = match[4][1:(len(match[4]) - 1)].split(",")
        predicates.append(Predicate(i, lemma, pos, args, term_id))

    return predicates


def __path_exists__(source, target, predicates, arg_predicates, max_path_length):
    """

    predicates : pred_id -> predicate map
    arg_predicates  : argument -> list of predicate where this arg appears

    """

    visited = set()

    source_arg = source.args[1] if (source.pos == "nn" or source.pos == "n") else source.args[0]
    target_arg = target.args[1] if (target.pos == "nn" or target.pos == "n") else target.args[0]

    if source_arg in target.args:
        return True

    if target_arg in source.args:
        return True

    if max_path_length == 0:
        return False

    visited = set([source.p_id, target.p_id])
    # candidates = [pred for pred in arg_predicates[source_arg] if pred.p_id not in visited]
    candidates = []
    for pred in arg_predicates[source_arg]:
        if pred.p_id not in visited:
            candidates.append(pred)

    visited.update([pred.p_id for pred in candidates])

    iter = 1
    while len(candidates) > 0:
        if iter > max_path_length:
            return False
        iter += 1
        next_candidates = []

        for candidate in candidates:

            # check candidate
            if target_arg in candidate.args:
                return True

            # add its neighbours to next candidates
            for arg in candidate.args:
                arg_preds = arg_predicates[arg]
                for pred in arg_preds:
                    if pred.p_id not in visited:
                        next_candidates.append(pred)
                        visited.add(pred.p_id)

        candidates = next_candidates

    return False