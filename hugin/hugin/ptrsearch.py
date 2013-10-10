#!/usr/bin/env python
# coding: utf-8

# Copyright (C) USC Information Sciences Institute
# Author: Vladimir M. Zaytsev <zaytsev@usc.edu>
# URL: <http://nlg.isi.edu/>
# For more information, see README.md
# For license information, see LICENSE


"""
Definitions:
    
    TS  - triples set (store) {τ}
    TD  - terms dictionary {w}
    
    * Triple         - tuple τ = <rt, a_1, a_2, ..., a_n>, where
    
                      + rt  - relation type
                      + a_i - i's argument term
                      + F_t - frequency of triple τ in store TS

    * args(τ)        - ordered set a_1, a_2, .., a_n of arguments of τ

    * freq(τ)        - frequency of triple τ in TS

    * Pattern        - pattern α is tuple <RT, A_1, A_2, .., A_k, POS^{RT}_{k+1}, A_{k+2}, A_{k+3}.., A_n>

                       + RT - relation type
                       + A_i - i's argument term
                       + POS^{RT}_{k+1} - set of possible part of speech tags {k+1}'s argument of relation RT

    * triples(α)     - set of triples <rt, a_1, a_2, .., a_{k-1}, x, a_{k+1}, a_{k+2} .., a_n, f> \in TS, such that:

                        rt  = RT
                        a_i = A_i, i=1..n, i =/= k
                        x   - any terms, such that pos(X) \in POS^{RT}_{k+2}
                        f   - any frequency
    
    * triple(α, w)   - triple τ \in triples(α) such that: a_{k + 1} = w

    * norm_freq_w(α) - normalized frequency of pattern α by term w
    
                        norm_freq_w(α) =           freq(triple(α, w))
                                             ––––––––––––––––––––––––––––––
                                             Σ_{τ \in triples(α)} {freq(τ)}

    * norm_freq_α(w) - normalized frequency of term w by pattern α

                        norm_freq_α(w) =       freq(triple(α, w))
                                            –––––––––––––––––––––––  – where T_w set of triples: {τ | w \in args(τ)}
                                            Σ_{τ \in T_w} {freq(τ)}


"""

import logging
import StringIO

from hugin.pos import POS_ID_NAME_MAP
from hugin.relsearch import REL_POS_MAP
from hugin.relsearch import REL_ID_NAME_MAP
from hugin.sourcesearch import PatternSearchQuery


class PatternCollection(object):
    
    def __init__(self, term_id, triples):
        self.triples = triples
        self.term_id = term_id
        self.patterns = []
        for triple in self.triples:
            pattern = Pattern(triple, term_id)
            self.patterns.append(pattern)

    def do_filter(self, stop_list):
        new_patterns = filter(lambda pt: not pt.is_light(stop_list), self.patterns)
        logging.info("FILTERED %d -> %d PATTERNS" % (len(self.patterns), len(new_patterns)))
        self.patterns = new_patterns
        
    def do_norm_freq(self, triple_store_explorer):
        for p in self.patterns:
            p.compute_norm_freq(triple_store_explorer)
    
    def sort(self, key=lambda pattern: -pattern.norm_freq):
        self.patterns.sort(key=key)
        
    def debug_output(self, o_file, engine, min_term_count=5):
        for i, p in enumerate(self.patterns):
            if len(p.terms) < min_term_count:
                continue
            o_file.write("%d\t%.8f\t%s\t%d\t" % (i, p.norm_freq, p.pprint(engine), len(p.terms)))
            for term_id, term_freq, tr_count, norm_freq in p.terms:
                o_file.write("%s(f=%d,c=%d,nf=%.8f) " % (engine.id_term_map[term_id], term_freq, tr_count, norm_freq))
            o_file.write("\n")
    
    def output_matrix(self, engine, matrix_fl, patterns_fl, terms_fl, norm=1, max_patters=100, max_terms=100):
        
        sparse_matrix = dict()

        pattern_key_index_map = dict()
        index_pattern_key_map = dict()
        term_id_index_map = dict()  # term_id -> column map
        index_term_id_map = dict()  # column -> term_id map

        self.patterns = self.patterns[0:min(max_patters, len(self.patterns))]
        
        for pattern in self.patterns:
            column = dict()
            if pattern.key not in pattern_key_index_map:
                pattern_index = len(pattern_key_index_map)
                pattern_key_index_map[pattern.key] = pattern_index
                index_pattern_key_map[pattern_index] = pattern
            else:
                pattern_index = pattern_key_index_map[pattern.key]

            terms = pattern.terms[0:min(max_terms, len(pattern.terms))]
            for term_id, freq, count, norm_freq in terms:
                
                if term_id not in term_id_index_map:
                    term_index = len(term_id_index_map)
                    term_id_index_map[term_id] = term_index
                    index_term_id_map[term_index] = term_id
                else:
                    term_index = term_id_index_map[term_id]
                
                if norm == 1:
                    measure = norm_freq
                else:
                    measure = freq

                column[term_index] = measure
            
            sparse_matrix[pattern_index] = column

        logging.info("OUTPUT TERMS IDs (%s) TO %r" % (len(term_id_index_map), terms_fl))
        for i in xrange(len(index_term_id_map)):
            term_id = index_term_id_map[i]
            terms_fl.write("%d,%s\n" % (i, engine.id_term_map[term_id]))

        logging.info("OUTPUT PATTERNS IDs (%s) TO %r" % (len(pattern_key_index_map), patterns_fl))
        for i in xrange(len(pattern_key_index_map)):
            pattern = index_pattern_key_map[i]
            patterns_fl.write("%d,%s\n" % (i, pattern.pprint(engine)))
        
        logging.info("OUTPUT MATRIX (%dx%d) TO %r" % (len(term_id_index_map), len(pattern_key_index_map), matrix_fl))
        for i in xrange(len(pattern_key_index_map)):
            for j in xrange(len(term_id_index_map)):
                if j in sparse_matrix[i]:
                    matrix_fl.write("%.16f " % sparse_matrix[i][j])
                else:
                    matrix_fl.write("0 ")
            matrix_fl.write("\n")


class Pattern(object):

    def __init__(self, triple, key_term):
        self.key_term = key_term
        self.triple = triple
        self.rel_type = triple[0]
        self.args = []  # args = [(i, term)]
        self.key = StringIO.StringIO()
        self.key.write("<")
        self.key.write(str(self.rel_type))
        self.key.write("-")
        self.terms = []
        for i in range(1, len(triple) - 1):
            if triple[i] >= 0 and triple[i] != key_term:
                self.args.append((i, triple[i]))
                self.key.write(str(i))
                self.key.write("-")
                self.key.write(str(triple[i]))
                if i != len(triple) - 2:
                    self.key.write("-")
            if triple[i] == key_term:
                self.key_term_i = i
                pos = REL_POS_MAP[self.rel_type][i - 1]
                self.args.append((i, POS_ID_NAME_MAP[pos]))
        self.key.write(">")
        self.key = self.key.getvalue()
        self.freq = triple[-1]
        self.norm_freq = -1
        
    def is_light(self, stop_list):
        non_ligth = 0
        for i, term_id in self.args:
            if i == self.key_term_i:
                continue
            if term_id not in stop_list:
                non_ligth += 1
        return non_ligth == 0

    def compute_norm_freq(self, engine, threshold=5.0, min_tr_count = 3):
        query = PatternSearchQuery(self.key_term, self.triple)
        triples = query.find_triples(engine, strict=False)
        total_freq = self.freq
        for tr in triples:
            tr_key_term = tr[self.key_term_i]
            tr_freq = tr[-1]
            if tr_key_term < 0 or tr_freq < threshold or tr_key_term == self.key_term:
                continue
            total_freq += tr_freq
            tr_key_term_triples = engine.search(arg_query=(tr_key_term,))
            if len(tr_key_term_triples) < 3:
                continue
            tr_key_term_triples_freq = sum([ttr[-1] for ttr in tr_key_term_triples])
            tr_key_term_norm_freq = float(tr_freq) / float(tr_key_term_triples_freq)
            self.terms.append((tr_key_term, tr_freq, len(tr_key_term_triples), tr_key_term_norm_freq))
        self.terms.sort(key=lambda t: -t[-1])
        self.norm_freq = float(self.freq) / float(total_freq)

    def pprint(self, engine):
        pstr = StringIO.StringIO()
        pstr.write("{")
        pstr.write(REL_ID_NAME_MAP[self.rel_type])
        pstr.write(";")
        terms = ";".join([engine.id_term_map[tid] if isinstance(tid, int) else tid for _, tid in self.args])
        pstr.write(terms)
        pstr.write("}")
        return pstr.getvalue()

