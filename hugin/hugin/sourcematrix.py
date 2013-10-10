#!/usr/bin/env python
# coding: utf-8

# Copyright (C) USC Information Sciences Institute
# Author: Vladimir M. Zaytsev <zaytsev@usc.edu>
# URL: <http://nlg.isi.edu/>
# For more information, see README.md
# For license information, see LICENSE

import logging

from hugin.ptrsearch import Pattern


def extract_source_matrix(potential_sources, engine, o_term_fl, o_pattern_fl, o_matrix_fl):
    sparse_matrix = dict()
    pattern_key_id_map = dict()
    pattern_id_key_map = dict()
    term_id_cid_map = dict()  # term_id -> column map
    term_cid_id_map = dict()  # column -> term_id map
    for ps in potential_sources:
        column = dict()  # [(pattern, measure)]
        for triple, norm_freq in ps.triples:
            pattern = Pattern(triple, ps.source_id)
            measure = norm_freq
            if pattern.key not in pattern_key_id_map:
                pattern_id = len(pattern_key_id_map)
                pattern_key_id_map[pattern.key] = pattern_id
                pattern_id_key_map[pattern_id] = pattern
            else:
                pattern_id = pattern_key_id_map[pattern.key]
            column[pattern_id] = measure
        if ps.source_id not in term_id_cid_map:
            column_id = len(term_id_cid_map)
            term_id_cid_map[ps.source_id] = column_id
            term_cid_id_map[column_id] = ps.source_id
        else:
            column_id = term_id_cid_map[ps.source_id]
        sparse_matrix[column_id] = column

    logging.info("OUTPUT SOURCES IDs (%s) TO %r" % (len(term_cid_id_map), o_term_fl))
    for i in xrange(len(term_cid_id_map)):
        term_id = term_cid_id_map[i]
        o_term_fl.write("%d,%d,%s\n" % (i, term_id, engine.id_term_map[term_id]))

    logging.info("OUTPUT PATTERNS IDs (%s) TO %r" % (len(pattern_id_key_map), o_pattern_fl))
    for i in xrange(len(pattern_id_key_map)):
        pattern = pattern_id_key_map[i]
        o_pattern_fl.write("%d,%s,%s\n" % (i, pattern.pprint(engine), pattern.key))

    logging.info("OUTPUT MATRIX (%dx%d) TO %r" % (len(term_cid_id_map), len(pattern_id_key_map), o_pattern_fl))
    for i in xrange(len(term_cid_id_map)):
        for j in xrange(len(pattern_id_key_map)):
            if j in sparse_matrix[i]:
                o_matrix_fl.write("%.16f " % sparse_matrix[i][j])
            else:
                o_matrix_fl.write("0 ")
        o_matrix_fl.write("\n")
