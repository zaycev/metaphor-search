# coding: utf-8
# Author: Vladimir M. Zaytsev <zaytsev@usc.edu>

import re
import json
import StringIO as stringio
import xml.dom.minidom as minidom

from sear.index import Document
from sear.index import IndexRecord
from sear.utils import StreamParser
from sear.index import DocumentIndexer

from metaphor.ruwac import RuwacDocument

from nltk.stem.snowball import SpanishStemmer
from nltk.stem.lancaster import LancasterStemmer
from nltk.tokenize import wordpunct_tokenize, sent_tokenize


class GigawordStream(object):
    DOC_OPENNING_TAG = "<DOC>"
    DOC_CLOSING_TAG = "</DOC>"

    def __init__(self, in_fl_stream):
        self.string_buffer = None
        self.in_fl_stream = in_fl_stream

    def close(self):
        self.in_fl_stream.close()
        self.in_fl_stream = None

    @staticmethod
    def open(in_fl_path):
        return GigawordStream(open(in_fl_path, "rb"))

    def __iter__(self):
        for line in self.in_fl_stream:

            if line.startswith(self.DOC_OPENNING_TAG):
                self.string_buffer = stringio.StringIO()
                self.string_buffer.write(line)

            elif line.startswith(self.DOC_CLOSING_TAG):
                self.string_buffer.write(line)
                xml_string = self.string_buffer.getvalue()
                self.string_buffer = None
                yield xml_string

            elif self.string_buffer is not None:
                self.string_buffer.write(line)

        if self.string_buffer is not None:
            yield self.string_buffer.getvalue()


class GigawordParser(StreamParser):

    def __init__(self, language):
        self.next_id = 0
        self.language = language
        if language == "es":
            self.stemmer = SpanishStemmer()
        elif language == "en":
            self.stemmer = LancasterStemmer()
        else:
            raise Exception("Unsupported language %s" % language)

    def init_id_counter(self, initial):
        self.next_id = initial

    def new_id(self):
        new_id = self.next_id
        self.next_id += 1
        return new_id

    def parse_raw(self, xml_str):
        xml = minidom.parseString(xml_str)
        if self.language == "es":
            url = "gigaword:" + xml.getElementsByTagName("DOC")[0].attributes["id"].value
        else:
            url = "<NONE>"
        if self.language == "es":
            title = xml.getElementsByTagName("HEADLINE")[0].firstChild.nodeValue
        else:
            url = "<NONE>"
        text = stringio.StringIO()
        for node in xml.getElementsByTagName("TEXT")[0].childNodes:
            if len(node.childNodes) > 0:
                text.write(node.firstChild.nodeValue)
        content = text.getvalue()
        terms = set([t.lower().encode("utf-8") for s in sent_tokenize(content)
                                               for t in wordpunct_tokenize(s)])
        return RuwacDocument(self.new_id(), url, title, content, terms)









