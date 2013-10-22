#!/usr/bin/env python
# coding: utf-8

# Copyright (C) USC Information Sciences Institute
# Author: Vladimir M. Zaytsev <zaytsev@usc.edu>
# URL: <http://nlg.isi.edu/>
# For more information, see README.md
# For license information, see LICENSE

import re

SENT_RE = re.compile("((\[.+?\]\:)?([^ .]+?)(\-[a-z]+)?(\([,a-z0-9]+?\)))")


class Predicate(object):

    def __init__(self, p_id, lemma, pos, args):
        self.p_id = p_id
        self.lemma = lemma
        self.pos = pos
        self.args = args

    def __repr__(self):
        return "<Predicate(%d, %s, %s)>" % (
            self.p_id,
            self.lemma,
            (" " + self.pos) if self.pos else ""
        )

def find_path(source_lemma, target_lemma, sentence, max_path_length=0):
    predicates = parse_sent(sentence)

    sources = [pred for pred in predicates if pred.lemma == source_lemma]
    targets = [pred for pred in predicates if pred.lemma == target_lemma]
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
                i, j = (target.p_id, source.p_id) if target.p_id < source.p_id else (source.p_id, target.p_id)
                return i, j, True
    return None, None, False


def parse_sent(lf_text):
    matches = SENT_RE.findall(lf_text)
    predicates = []
    for i, match in enumerate(matches):
        lemma = match[2]
        pos = match[3][1:]
        args = match[4][1:(len(match[4]) - 1)].split(",")
        predicates.append(Predicate(i, lemma, pos, args))
    return predicates


def __path_exists__(source, target, predicates, arg_predicates, max_path_length):
    """

    predicates : pred_id -> predicate map
    arg_predicates  : argument -> list of predicate where this arg appears

    """

    visited = set()

    source_arg = source.args[1] if source.pos == "nn" else source.args[0]
    target_arg = target.args[1] if target.pos == "nn" else target.args[0]

    if source_arg in target.args:
        return True

    if target_arg in source.args:
        return True

    if max_path_length == 0:
        return False

    visited = set([source.p_id, target.p_id])
    candidates = [pred for pred in arg_predicates[source_arg] if pred.p_id not in visited]
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