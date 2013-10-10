# coding: utf-8
# Author: Vladimir M. Zaytsev <zaytsev@usc.edu>

import re
import json
import pickle
import numpy as np

from StringIO import StringIO as stringio

from sear.index import Document
from sear.index import IndexRecord
from sear.utils import StreamParser
from sear.index import DocumentIndexer

from hugin.pos import POS_NAMES
from hugin.pos import POS_NAME_ID_MAP
from hugin.pos import POS_ID_NAME_MAP
from hugin.relsearch import REL_NAME_ID_MAP
from hugin.relsearch import REL_ID_NAME_MAP

from hugin.minlf import MinLFSParser


class Triplet(Document):
    TRP_DELIMITER = chr(255)    # delimiter for triple tokens
    TRM_DELIMITER = chr(254)    # delimiter for pos-term tokens
    EMPTY_ARGUMENT = chr(253)   # empty-argument marker

    def __init__(self, t_id, rel_type, args, freq):
        """

        Class representing semantic triplet (arguments + relation) with frequency.
        Despite the fact it is called "triplet", the number of arguments can be any.

        @type t_id: int
        @param t_id: Unique id of triplet id in corpus.

        @type rel_type: str \from *RELATION_NAMES*
        @param rel_type: Triplet relation type.

        @type args: [(str, str \from *POS_NAMES*)]
        @param args: Ordered list of tuples word-part_of_speech_tag.

        @type freq: int
        @param freq: Triplet corpus frequency.

        """
        #super(Triplet, self).__init__(triplet_id)
        self.doc_id = t_id

        if rel_type is None:
            self.frequency = -1
            self.rel_type = None
            self.arguments = None
            return

        #if rel_type in RELATION_NAMES:
        #    self.rel_type = REL_NAME_ID_MAP[rel_type]
        #else:
        #    raise TypeError("Unknown relation type %r" % rel_type)
        self.rel_type = REL_NAME_ID_MAP[rel_type]

        self.arguments = []
        self.frequency = freq
        for term_pos in args:
            if term_pos is None:
                self.arguments.append(None)
            else:
                term, pos = term_pos
                if pos in POS_NAMES:
                    self.arguments.append((term, POS_NAME_ID_MAP[pos]))
                else:
                    raise TypeError("Unknown part-of-speech tag: %r" % term_pos[1])
        self.idx_terms = list(set([tp[0] for tp in self.arguments if tp is not None]))

    def fromstring(self, string):
        tokens = string.split(self.TRP_DELIMITER)
        self.rel_type = int(tokens[0])
        self.frequency = int(tokens[1])
        self.arguments = []
        for i in xrange(2, len(tokens)):
            if tokens[i] == self.EMPTY_ARGUMENT:
                self.arguments.append(None)
            else:
                term_pos = tokens[i].split(self.TRM_DELIMITER)
                self.arguments.append((term_pos[0], int(term_pos[1])))
        self.idx_terms = list(set([tp[0] for tp in self.arguments if tp is not None]))

    def tostring(self):
        string = stringio()
        string.write(str(self.rel_type))
        string.write(self.TRP_DELIMITER)
        string.write(str(self.frequency))
        for term_pos in self.arguments:
            string.write(self.TRP_DELIMITER)
            if term_pos is None:
                string.write(self.EMPTY_ARGUMENT)
            else:
                string.write(term_pos[0])
                string.write(self.TRM_DELIMITER)
                string.write(term_pos[1])
        return string.getvalue()

    def terms(self):
        return self.idx_terms

    def __str__(self):
        string = stringio()
        string.write("<")
        string.write(REL_ID_NAME_MAP[self.rel_type])
        string.write(" ")
        for term_pos in self.arguments:
            if term_pos is None:
                string.write("None")
            else:
                string.write("%s-%s" % (term_pos[0], POS_ID_NAME_MAP[term_pos[1]]))
            string.write(" ")
        string.write(str(self.frequency))
        string.write(">")
        return string.getvalue()


class TripletIndexRecord(IndexRecord):

    def __init__(self, rel_type_id, arguments, frequency):
        """

        Class for compact representation of indexed triplet.

        @type rel_type_id: int
        @param rel_type_id: Id of triplet relation type.

        @type arguments: [(int, int)] | None
        @param arguments: Sequence of pairs (term_id, pos_tag_id) or None.

        @type frequency: int
        @param frequency: Triplet corpus frequency.

        """
        super(TripletIndexRecord, self).__init__()
        self.rel_type_id = rel_type_id
        self.arguments = arguments
        self.frequency = frequency

    def property_vectors(self):
        vectors = []
        for i in xrange(0, len(self.arguments)):
            if self.arguments[i] is None:
                continue
            else:
                vectors.append(np.array((
                    self.arguments[i][0],
                    i,
                    self.rel_type_id,
                    self.arguments[i][1],
                    self.frequency,
                ), dtype=np.int32))
        return vectors


class TripletIndexer(DocumentIndexer):

    def __init__(self, lexicon):
        self.lexicon = lexicon

    def index_item(self, triplet):
        arguments = [None if term_pos is None else (self.lexicon.get_id(term_pos[0]), term_pos[1])
                     for term_pos in triplet.arguments]
        return TripletIndexRecord(triplet.rel_type, arguments, triplet.frequency)


class TripletParser(StreamParser):
    CSV_TRP_DELIMITER = ","
    CSV_POS_DELIMITER = "-"
    CSV_EMPTY_TERM = "<NONE>"
    CSV_IGNORE_TERM = "<->"

    def __init__(self):
        self.next_id = 0

    def init_id_counter(self, initial):
        self.next_id = initial

    def new_id(self):
        new_id = self.next_id
        self.next_id += 1
        return new_id

    def parse_raw(self, line):
        """

        Maps CSV lines into list of [(term, term_index_record, ...)]
        CSV should be formed like this:

        <relation_name>,<term_1>-<pos_1>,...,<term_k>-<pos_k>,<freq>

        If term is unknown, use <NONE> marker. For example:

        subj_verb,речь-NN,идти-VB,<->,<->,<->,85846

        """
        row = line.split(self.CSV_TRP_DELIMITER)
        rel_name = row[0]
        frequency = int(row[-1])
        arguments = []
        properties = []
        for i in xrange(1, len(row) - 2):
            if row[i] == self.CSV_EMPTY_TERM:
                arguments.append(None)
                properties.append(None)
            elif row[i] == self.CSV_IGNORE_TERM:
                continue
            else:
                term_and_pos = row[i].split(self.CSV_POS_DELIMITER)
                pos_name = term_and_pos[-1]
                term = "".join(term_and_pos[0:(len(term_and_pos) - 1)])
                arguments.append((term, pos_name))
        triplet = Triplet(self.new_id(), rel_name, arguments, frequency)
        return triplet


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
        doc_json = json.loads(string)
        self.url = doc_json["u"]
        self.title = doc_json["t"]
        self.content = doc_json["c"]
        self.idx_terms = doc_json["i"]

    def tostring(self):
        return json.dumps({
            "u": self.url,
            "t": self.title,
            "c": self.content,
            "i": self.idx_terms,
        })

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
        for i in xrange(len(document.idx_terms)):
            if term_ids[i] == -1:
                print document.idx_terms[i]
                exit(0)
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
        url, title = header[0]
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


class LFSentenceStream(object):

    def __init__(self, sentences_fl_path):
        self.parser = MinLFSParser(open(sentences_fl_path, "rb"))
        self.__iter__ = self.parser.__iter__


class LFSentenceParser(StreamParser):
    """

        Class used to wrap actual the LF parser.

    """

    def __init__(self):
        super(LFSentenceParser, self).__init__()
        self.next_id = 0

    def parse_raw(self, lf_sentence):
        terms = [p.lemma.encode("utf-8") for p in lf_sentence.predicates if p.lemma is not None]
        return LFSDocument(self.new_id(), terms, lf_sentence)


class LFSDocument(Document):

    def __init__(self, d_id, terms, lf_sentence):
        """

        @type d_id: int
        @param d_id: Unique id of sentence id in corpus.

        @type terms: [str]
        @param terms: List of terms to be indexed.

        @type content: <hugin.lfparser.Sentence>
        @param content: Sentence in FOL form.

        """
        self.doc_id = d_id
        self.lf_sentence = lf_sentence
        if terms is not None:
            self.idx_terms = list(set(terms))

    def fromstring(self, string):
        terms, lf_sentence = pickle.loads(string)
        self.idx_terms = terms
        self.lf_sentence = lf_sentence

    def tostring(self):
        return pickle.dumps((self.idx_terms, self.lf_sentence))

    def terms(self):
        return self.idx_terms

    def __str__(self):
        return "<LFSDocument(id=%d size=%d)>" % (self.doc_id, len(self.idx_terms))


class LFSIndexRecord(IndexRecord):

    def __init__(self, term_ids):
        """

        Class for compact representation of indexed sentence index record.

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