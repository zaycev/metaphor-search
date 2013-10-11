#!/usr/bin/env python
# coding: utf-8

# Copyright (C) USC Information Sciences Institute
# Author: Vladimir M. Zaytsev <zaytsev@usc.edu>
# URL: <http://nlg.isi.edu/>
# For more information, see README.md
# For license information, see LICENSE

import re


SENT_RE = re.compile("((\[.+?\]\:)?([^ .]+?)(\-[a-z]+)?(\([,a-z0-9]+?\)))")


def parse_sent(lf_text):
    matches = SENT_RE.findall(lf_text)
    predicates = []
    for p in matches:
        lemma = p[2]
        #pos = p[3]
        args = p[4][1:(len(p[4]) - 1)].split(",")
        predicates.append((lemma, args))
    return predicates


def __find_path(source, target, states, transitions):
    visited = set()
    visit_this_next = [source]
    while len(visit_this_next) > 0:
        visit_this_next
        new_visit_this = []
        for state in visit_this_next:
            visited.add(state)
            state_transitions = transitions[state][1]
            for t in state_transitions:
                new_states = states[t]
                for new_state in new_states:
                    if new_state not in visited:
                        if state == target:
                            return True
                        new_visit_this.append(new_state)
            visit_this_next = new_visit_this
    return False


def find_path(source, target, sentence):
    states = parse_sent(sentence)
    transitions = dict()
    sources_i = [i for i, (lemma, args) in enumerate(states) if lemma == source]
    targets_i = [i for i, (lemma, args) in enumerate(states) if lemma == target]
    for i, (lemma, args) in enumerate(states):
        for arg in args:
            if arg in transitions:
                transitions[arg].append(i)
            else:
                transitions[arg] = [i]
    for target_i in targets_i:
        for source_i in sources_i:
            found = __find_path(source_i, target_i, transitions, states)
            if found:
                return found
    return False