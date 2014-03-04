# coding: utf-8
# Author: Vladimir M. Zaytsev <zaytsev@usc.edu>
# from __future__ import print_function

import abc
import sys
import logging
import datetime


class DocumentStream(object):

    @abc.abstractmethod
    def __iter__(self):
        return NotImplementedError("")


class StreamParser(object):

    def __init__(self):
        self.next_id = 0

    def init_id_counter(self, initial):
        self.next_id = initial

    def new_id(self):
        new_id = self.next_id
        self.next_id += 1
        return new_id

    @abc.abstractmethod
    def parse_raw(self, raw_document):
        return NotImplemented("StreamParser is interface class")


class IndexingPipeline(object):

    def __init__(self, lexicon=None, index=None, storage=None):
        """

        """
        self.index = index
        self.lexicon = lexicon
        self.storage = storage

    def index_stream(self, document_stream, stream_parser, item_indexer):
        """

        """
        mb_size = 1024 ** 2
        document_i = 0
        total_bytes = 0.0
        start_time = datetime.datetime.now()
        log_template = "Processed Documents: %d;  " \
                       "Collected Terms: %d;  " \
                       "Processed: %.2fMB;  " \
                       "Work Time: %ds"

        for raw_document in document_stream:

            try:
                document = stream_parser.parse_raw(raw_document)
            except Exception:
                logging.error("Error while parsing line (#%d): %s" % (document_i, raw_document))
                import traceback
                traceback.print_exc()
                document_i += 1
                continue

            doc_terms = document.terms()
            unique_terms = set(doc_terms)
            new_terms = [term for term in unique_terms if self.lexicon.get_id(term) == -1]

            self.lexicon.count_terms(doc_terms)

            index_record = item_indexer.index_item(document)

            try:
                raw_document = document.tostring()
                self.index.add_to_index(document.id, index_record)
                self.storage.add_terms(self.lexicon, new_terms)
                self.storage.add_document(document.id, raw_document)
            except Exception:
                import traceback
                logging.error("Error while serializing document. %r" % traceback.format_exc())
                continue

            total_bytes += len(raw_document) + 1
            total_terms = len(self.lexicon)

            if document_i % 10000 == 0:
                cur_time = datetime.datetime.now()
                time_delta = cur_time - start_time
                logging.info(log_template % (
                    document_i,
                    total_terms,
                    total_bytes / mb_size,
                    time_delta.total_seconds()
                ))

                if document_i % 10000000:
                    self.lexicon.dump()

            document_i += 1

        self.index.dump_and_merge()
        self.storage.flush_term_buffers()
        self.storage.flush_doc_buffers()

        sys.stdout.write("\n")
