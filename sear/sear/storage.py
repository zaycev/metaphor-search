# coding: utf-8
# Author: Vladimir M. Zaytsev <zaytsev@usc.edu>

import os
import json
import leveldb
import logging
import numpy as np


class COMPRESSION:

    NONE = "NONE"
    ZLIB = "ZLIB"
    LZMA = "LZMA"
    LZ4R = "LZ4R"
    LZ4H = "LZ4H"


class LdbStorage(object):
    TERMS_FL = "terms.ldb"
    DOCS_FL = "docs.ldb"
    META_FL = "storage.json"
    BUFF_SZ = 4024 * 512

    def __init__(self, root_dir, terms_fl=None, docs_fl=None):

        self.root = root_dir
        self.terms_fl = terms_fl if terms_fl is not None else os.path.join(self.root, self.TERMS_FL)
        self.docs_fl = docs_fl if docs_fl is not None else os.path.join(self.root, self.DOCS_FL)
        self.meta_fl = os.path.join(self.root, self.META_FL)

        self.opened = False

        self.documents_number = 0                       # total number of documents in storage
        self.terms_number = 0                           # total number of terms in storage

        self.max_doc_flush_buffer_size = self.BUFF_SZ   # max number of items in doc buffer
        self.max_term_flush_buffer_size = self.BUFF_SZ  # max number of items in term buffer
        self.doc_buffer_size = None                     # number of items in doc buffer
        self.term_buffer_size = None                    # number of items in term buffer
        self.max_term_size = 64                         # max size of term in storage
        self.max_doc_size = 256                         # max size of document in storage

        self.doc_id_flush_buffer = None                 # int64 array used to cache doc ids before flushing to disk
        self.term_id_flush_buffer = None                # int64 array used to cache term ids before flushing to disk
        self.doc_flush_buffer = None                    # string array used to cache documents before flushing to disk
        self.term_flush_buffer = None                   # string array used to cache terms before flushing to disk

        self.term_cache = None                          # term read cache
        self.doc_cache = None                           # term read cache

        self.compression = COMPRESSION.NONE             #
        self.doc_compression_block = 0                  #
        self.term_compression_block = 0                 #
        self.compression_level = 9                      #

        self.compress = None                            # compression func,  will be assigned in <open> method
        self.decompress = None                          # decompression func, will be assigned in <open> method

        self.terms_ldb = None                           # LDB instance to store terms
        self.docs_ldb = None                            # LDB instance to store docs

        if self.doc_compression_block > 0 and self.max_doc_flush_buffer_size % self.doc_compression_block != 0:
            raise Exception("Buffer size should be N times compression block")
        if self.term_compression_block > 0 and self.max_term_flush_buffer_size % self.term_compression_block != 0:
            raise Exception("Buffer size should be N times compression block")

    def dumps_meta(self):
        return json.dumps({
            "documents_number":             self.documents_number,
            "terms_number":                 self.terms_number,
            "max_doc_flush_buffer_size":    self.max_doc_flush_buffer_size,
            "max_term_flush_buffer_size":   self.max_term_flush_buffer_size,
            "max_doc_size":                 self.max_doc_size,
            "max_term_size":                self.max_term_size,
            "compression":                  self.compression,
            "doc_compression_block":        self.doc_compression_block,
            "term_compression_block":       self.term_compression_block,
            "compression_level":            self.compression_level,
        }, indent=8)

    def dump_meta(self):
        logging.info("Storage: dumping meta.")
        meta_file = open(self.meta_fl, "wb")
        meta_file.write(self.dumps_meta())
        meta_file.close()

    def loads_meta(self, meta_json):
        meta = json.loads(meta_json)
        self.documents_number = meta["documents_number"]
        self.terms_number = meta["terms_number"]
        self.max_doc_size = meta["max_doc_size"]
        self.max_term_size = meta["max_term_size"]
        self.max_doc_flush_buffer_size = meta["max_doc_flush_buffer_size"]
        self.max_term_flush_buffer_size = meta["max_term_flush_buffer_size"]
        self.compression = meta["compression"]
        self.doc_compression_block = meta["doc_compression_block"]
        self.term_compression_block = meta["doc_compression_block"]
        self.compression_level = meta["compression_level"]

    def load_meta(self):
        logging.info("Storage: loading meta.")
        meta_file = open(self.meta_fl, "rb")
        meta_json = meta_file.read()
        meta_file.close()
        self.loads_meta(meta_json)

    def init_db(self):
        if not os.path.exists(self.root):
            os.mkdir(self.root)
        self.dump_meta()

    def open_db(self):
        self.terms_ldb = leveldb.LevelDB(self.terms_fl)
        self.docs_ldb = leveldb.LevelDB(self.docs_fl)

        self.doc_buffer_size = 0
        self.term_buffer_size = 0

        #self.doc_flush_buffer = np.empty(self.max_doc_flush_buffer_size, dtype="S%d" % self.max_doc_size)
        self.doc_flush_buffer = [None] * self.max_doc_flush_buffer_size
        self.term_flush_buffer = np.empty(self.max_term_flush_buffer_size, dtype="S%d" % self.max_term_size)
        self.doc_id_flush_buffer = np.empty(self.max_doc_flush_buffer_size, dtype=np.int64)
        self.term_id_flush_buffer = np.empty(self.max_term_flush_buffer_size, dtype=np.int64)

        if self.compression == COMPRESSION.NONE:
            self.compress = lambda string: string
            self.decompress = lambda string: string
        elif self.compression == COMPRESSION.ZLIB:
            import zlib
            self.compress = lambda string: zlib.compress(string, self.compression_level)
            self.decompress = lambda string: zlib.decompress(string)
        elif self.compression == COMPRESSION.LZMA:
            import backports.lzma as lzma
            self.compress = lambda string: lzma.compress(bytearray(string), format=lzma.FORMAT_RAW)
            self.decompress = lambda data: lzma.decompress(data, format=lzma.FORMAT_RAW)
        elif self.compression == COMPRESSION.LZ4R:
            import lz4
            self.compress = lambda string: lz4.compress(string)
            self.decompress = lambda string: lz4.decompress(string)
        elif self.compression == COMPRESSION.LZ4H:
            import lz4
            self.compress = lambda string: lz4.compressHC(string)
            self.decompress = lambda string: lz4.decompress(string)
        else:
            raise Exception("Wrong compression type %r" % self.compression)

    def close_db(self):
        logging.info("Storage: closing database.")
        self.flush_term_buffers()
        self.flush_doc_buffers()
        self.terms_ldb = None
        self.docs_ldb = None
        self.term_flush_buffer = None
        self.doc_flush_buffer = None
        self.doc_buffer_size = None
        self.term_buffer_size = None
        self.term_id_flush_buffer = None
        self.doc_id_flush_buffer = None
        self.compress = None
        self.decompress = None

    def flush_term_buffers(self):
        logging.info("Storage: flushing terms buffer [%d items]." % self.term_buffer_size)
        batch = leveldb.WriteBatch()
        for i in xrange(0, self.term_buffer_size):
            term_id = self.term_id_flush_buffer[i]
            term = self.term_flush_buffer[i]
            batch.Put(str(term_id), term)
        self.terms_number += self.term_buffer_size
        self.terms_ldb.Write(batch, sync=False)
        self.term_buffer_size = 0
        self.dump_meta()

    def flush_doc_buffers(self):
        logging.info("Storage: flushing documents buffer [%d items]." % self.doc_buffer_size)
        batch = leveldb.WriteBatch()
        for i in xrange(0, self.doc_buffer_size):
            doc_id = self.doc_id_flush_buffer[i]
            doc = self.doc_flush_buffer[i]
            batch.Put(str(doc_id), doc)
        self.documents_number += self.doc_buffer_size
        self.docs_ldb.Write(batch, sync=False)
        self.doc_buffer_size = 0
        self.dump_meta()

    def add_terms(self, lexicon, terms):
        for term in terms:
            term_id = lexicon.get_id(term)
            self.term_id_flush_buffer[self.term_buffer_size] = term_id
            self.term_flush_buffer[self.term_buffer_size] = term
            self.term_buffer_size += 1
            if self.term_buffer_size == self.max_term_flush_buffer_size:
                self.flush_term_buffers()

    def add_document(self, doc_id, doc_blob):
        self.doc_id_flush_buffer[self.doc_buffer_size] = doc_id
        self.doc_flush_buffer[self.doc_buffer_size] = doc_blob
        self.doc_buffer_size += 1
        if self.doc_buffer_size == self.max_doc_flush_buffer_size:
            self.flush_doc_buffers()

    def cache_terms(self):
        pass

    def cache_documents(self):
        pass

    def get_document(self, document_id):
        if self.docs_ldb is None:
            return Exception("Storage should be opened in order to retrieve documents.")
        return self.docs_ldb.Get(document_id)

    def get_term(self):
        pass


