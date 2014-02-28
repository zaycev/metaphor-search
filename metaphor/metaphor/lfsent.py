# coding: utf-8
# Author: Vladimir M. Zaytsev <zaytsev@usc.edu>

import json

from sear.index import Document
from sear.index import IndexRecord
from sear.utils import StreamParser
from sear.index import DocumentIndexer

from hugin.minlf import MinLFSParser
from hugin.minlf import MinBoxerLFSParser


class LFSentenceStream(object):

    def __init__(self, sentences_fl_path, language):
        if language == "rus" or language == "spa":
            self.parser = MinLFSParser(open(sentences_fl_path, "rb"))
        elif language == "eng":
            self.parser = MinBoxerLFSParser(open(sentences_fl_path, "rb"))
        else:
            raise Exception("Unsupported language: %s" % language)

    def __iter__(self):
        return self.parser.__iter__()


class LFSentenceParser(StreamParser):
    """

        Class used to wrap actual the LF parser.

    """

    def __init__(self):
        super(LFSentenceParser, self).__init__()
        self.next_id = 0

    def parse_raw(self, text_sent_terms):
        raw_text, lf_sent, terms = text_sent_terms
        return LFSDocument(self.new_id(), raw_text, lf_sent, terms)


class LFSDocument(Document):

    def __init__(self, d_id, raw_text, lf_sentence, terms):
        """

        Class to represent information about LF sentence which we want to store.

        @type d_id: int
        @param d_id: Unique id of sentence id in corpus.

        @type terms: [str]
        @param terms: List of terms to be indexed.

        @type lf_sentence:
        @param lf_sentence: Sentence in FOL form.

        """

        super(LFSDocument, self).__init__(d_id)
        self.idx_terms = terms
        self.raw_text = raw_text
        self.lf_sentence = lf_sentence
        if terms is not None:
            self.idx_terms = terms

    def fromstring(self, string):
        lfs_dict = json.loads(string)
        self.raw_text = lfs_dict["r"]
        self.idx_terms = lfs_dict["t"]
        self.lf_sentence = lfs_dict["s"]

    def tostring(self):
        lfs_json = json.dumps({
            "r": self.raw_text,
            "t": self.idx_terms,
            "s": self.lf_sentence,
        })
        return lfs_json

    def terms(self):
        return self.idx_terms

    def __str__(self):
        return "<LFSDocument(id=%d size=%d)>" % (self.doc_id, len(self.idx_terms))


class LFSIndexRecord(IndexRecord):

    def __init__(self, term_ids):
        """

        Class for compact representation of indexed sentence.

        """
        super(LFSIndexRecord, self).__init__()
        self.term_ids = term_ids

    def property_vectors(self):
        return [[term_id] for term_id in self.term_ids]


class LFSentenceIndexer(DocumentIndexer):

    def __init__(self, lexicon):
        self.lexicon = lexicon

    def index_item(self, document):
        term_ids = [self.lexicon.get_id(t) for t in document.idx_terms]
        return LFSIndexRecord(term_ids)