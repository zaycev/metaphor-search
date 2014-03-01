# coding: utf-8
# Author: Vladimir M. Zaytsev <zaytsev@usc.edu>

import os
import leveldb
import logging


class DictLexicon(object):
    TERM_FREQ_SEP = chr(255)
    LEX_DIR_NAME = "dict.lexicon.ldb"

    def __init__(self, root_dir):
        self.term_dict = dict()
        self.root_dir = root_dir
        self.lexicon_root = os.path.join(self.root_dir, self.LEX_DIR_NAME)
        self.ldb = leveldb.LevelDB(self.lexicon_root)

    def add_term(self, term):
        term_and_freq = self.term_dict.get(term)
        if term_and_freq is not None:
            term_and_freq[1] += 1
        else:
            new_term_id = len(self.term_dict)
            self.term_dict[term] = [new_term_id, 1]

    def count_terms(self, terms):
        for term in terms:
            self.add_term(term)

    def get_id(self, term):
        term_and_freq = self.term_dict.get(term)
        if term_and_freq is not None:
            return term_and_freq[0]
        return -1

    def dump(self):
        w_batch = leveldb.WriteBatch()
        total_wrote = 0
        for term, term_and_freq in self.term_dict.iteritems():
            w_batch.Put(term, str(term_and_freq[0]) + self.TERM_FREQ_SEP + str(term_and_freq[1]))
            total_wrote += 1
        self.ldb.Write(w_batch)
        logging.info("DictLexicon: wrote %d term to ldb" % total_wrote)

    def load(self):
        lexicon_root = os.path.join(self.root_dir, self.LEX_DIR_NAME)
        if not os.path.exists(lexicon_root):
            os.mkdir(lexicon_root)
            logging.warn("Lexicon file %s not exist. Skip.")
        if len(self) > 0:
            raise Exception("Non empty lexicon does not support reading")
        ldb = leveldb.LevelDB(lexicon_root)
        total_read = 0
        for term, term_and_freq in ldb.RangeIter():
            term_id, term_freq = term_and_freq.split(self.TERM_FREQ_SEP)
            term_id = int(term_id)
            term_freq = int(term_freq)
            self.term_dict[term] = [term_id, term_freq]
            total_read += 1
        logging.info("DictLexicon: read %d term from ldb" % total_read)

    def __len__(self):
        return self.term_dict.__len__()

    def __contains__(self, term):
        return self.term_dict.__contains__(term)