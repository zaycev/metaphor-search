# coding: utf-8
# Author: Vladimir M. Zaytsev <zaytsev@usc.edu>

import re
import lz4
import json


from sear.index import Document
from sear.index import IndexRecord
from sear.utils import StreamParser
from sear.index import DocumentIndexer


class RuwacStream(object):
    DOC_OPENNING_TAG = "<text"
    DOC_CLOSING_TAG = "</text"

    def __init__(self, ruwac_fl_stream):
        self.line_buffer = []
        self.ruwac_fl_stream = ruwac_fl_stream

    def close(self):
        self.ruwac_fl_stream.close()
        self.ruwac_fl_stream = None

    @staticmethod
    def open(ruwac_fl_path):
        return RuwacStream(open(ruwac_fl_path, "rb"))

    def __iter__(self):
        for line in self.ruwac_fl_stream:
            if line.startswith(self.DOC_OPENNING_TAG):
                self.line_buffer = [line]
            elif line.startswith(self.DOC_CLOSING_TAG):
                if len(self.line_buffer) > 0:
                    yield self.line_buffer
                else:
                    continue
            else:
                self.line_buffer.append(line)
        if len(self.line_buffer) > 0:
            yield self.line_buffer


class RuwacDocument(Document):

    def __init__(self, d_id, url, title, content, terms):
        """

        @type d_id: int
        @param d_id: Unique id of document id in corpus.

        @type terms: [str]
        @param terms: List of words to be inxed.

        @type content: <json object>
        @param content: Document content as JSON object.

        """
        self.doc_id = d_id
        self.url = url
        self.title = title
        self.content = content
        if terms is not None:
            self.idx_terms = list(set(terms))

    def fromstring(self, string):
        doc_json = json.loads(lz4.decompress(string))
        self.url = doc_json["u"]
        self.title = doc_json["t"]
        self.content = doc_json["c"]
        self.idx_terms = doc_json["i"]

    def tostring(self):
        return lz4.compressHC(json.dumps({
            "u": self.url,
            "t": self.title,
            "c": self.content,
            "i": self.idx_terms,
        }))

    def terms(self):
        return self.idx_terms

    def __str__(self):
        return "<RuwacDocument(id=%d url=%s)>" % (self.doc_id, self.url)


class RuwacIndexRecord(IndexRecord):

    def __init__(self, term_ids):
        """

        Class for compact representation of indexed ruwac document.

        """
        super(RuwacIndexRecord, self).__init__()
        self.term_ids = term_ids

    def property_vectors(self):
        return [[term_id] for term_id in self.term_ids]


class RuwacIndexer(DocumentIndexer):

    def __init__(self, lexicon):
        self.lexicon = lexicon

    def index_item(self, document):
        term_ids = [self.lexicon.get_id(t) for t in document.idx_terms]
        return RuwacIndexRecord(term_ids)


class RuwacParser(StreamParser):
    RUWAC_TOKEN_DELIMITER = "\t"
    RUWAC_DOC_HEADER_PTR = re.compile(".*id=\"(.+)\"\s+title=\"(.+)\".*")
    RUWAC_PUNCT_REL = "PUNC\n"

    def __init__(self):
        self.next_id = 0

    def init_id_counter(self, initial):
        self.next_id = initial

    def new_id(self):
        new_id = self.next_id
        self.next_id += 1
        return new_id

    def parse_raw(self, doc_lines):
        header = self.RUWAC_DOC_HEADER_PTR.findall(doc_lines[0])
        if len(header) == 2:
            url, title = header[0]
        else:
            url = "<NONE>"
            title = "<NONE>"
        terms = []
        content = [[]]
        for i in xrange(1, len(doc_lines)):
            tokens = doc_lines[i].split(self.RUWAC_TOKEN_DELIMITER)
            content[-1].append(tokens[0])
            if tokens[-1] != self.RUWAC_PUNCT_REL:
                terms.append(tokens[2])
            else:
                content.append([])
        return RuwacDocument(self.new_id(), url, title, content, terms)