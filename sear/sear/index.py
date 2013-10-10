# coding: utf-8
# Author: Vladimir M. Zaytsev <zaytsev@usc.edu>

import os
import gc
import abc
import json
import leveldb
import logging
import numpy as np


class Document(object):
    """

    """
    def __init__(self, doc_id):
        self.doc_id = doc_id

    @property
    def id(self):
        """

        Returns unique id of document.

        """
        return self.doc_id

    @abc.abstractmethod
    def tostring(self):
        """

        Returns a string representation of document.

        """
        return NotImplementedError("Document is abstract class")

    @abc.abstractmethod
    def fromstring(self, string):
        """

        Loads reproduces a document object from given string.

        """
        return NotImplementedError("Document is abstract class")

    @abc.abstractmethod
    def terms(self):
        """

        Returns list terms in document.

        """
        return NotImplementedError("Document is abstract class")


class IndexRecord(object):

    @abc.abstractmethod
    def property_vectors(self):
        """

        Returns property vectors. Vectors can be, for example like this: [<term, pos-tag, rel-type, freq>].
                                                                            ^       ^--------^--------^
                                                                            |       |
                                                                         Primory key| should always be a term id.
                                                                                    |
                                                                           Secondary indexes..

        So, index can used these properties in queries like this: search(pos-tag = NN, rel-type = NN-prep) -> [doc.id]


        """
        return NotImplementedError("IndexedDocument is abstract class")

    @abc.abstractmethod
    def tobytes(self):
        """

        Returns string representation of document.

        """
        return NotImplementedError("IndexedDocument is abstract class")

    @abc.abstractmethod
    def frombytes(self):
        """

        Returns string representation of document.

        """
        return NotImplementedError("IndexedDocument is abstract class")


class DocumentIndexer(object):

    @abc.abstractmethod
    def index_item(self, basic_document):
        return NotImplementedError("DocumentIndexer is abstract class")


class PostingList(object):
    GROW_SZ = 32
    GROW_DG = 1.6

    def __init__(self):
        self.size = 0
        self.capacity = self.GROW_SZ
        self.fields = None

    @staticmethod
    def create_and_init(field_properties):
        plist = PostingList()
        if field_properties is not None:
            plist.fields = [None] * len(field_properties)
            for i in xrange(len(field_properties)):
                plist.fields[i] = np.zeros(plist.capacity, dtype=field_properties[i][1])
        return plist

    @staticmethod
    def create_empty(fields_number):
        plist = PostingList()
        plist.fields = [None] * fields_number
        return plist

    def set_field(self, field_index, raw_field, property_type):
        self.fields[field_index] = np.fromstring(raw_field, property_type)

    def add(self, vector):
        if self.size == self.capacity:
            self.capacity += self.GROW_SZ
            #self.capacity = int(self.capacity * self.GROW_DG)
            for i in xrange(len(self.fields)):
                new_data = np.zeros(self.capacity, dtype=self.fields[i].dtype)
                new_data[:self.size] = self.fields[i]
                self.fields[i] = new_data
                self.fields[i][self.size] = vector[i]
        else:
            for i in xrange(len(self.fields)):
                self.fields[i][self.size] = vector[i]
        self.size += 1

    def __getitem__(self, item):
        result = []
        for field in self.fields:
            result.append(field[item])
        return result

    def __len__(self):
        return self.size


def dtype_to_name(dt):
    if dt == np.int8:
        return "i1"
    if dt == np.int16:
        return "i2"
    if dt == np.int32:
        return "i4"
    if dt == np.int64:
        return "i8"


def name_to_dtype(dt):
    if dt == "i1":
        return np.int8
    if dt == "i2":
        return np.int16
    if dt == "i4":
        return np.int32
    if dt == "i8":
        return np.int64


class InvertedIndex(object):
    INDEX_KEY_SEP = chr(255)
    BARRELS_DIR = "barrels.ldb"
    META_FILE = "index.json"
    BATCH_SZ = 4096 * 1024
    CACHE_SZ = 32000 * 1024

    def __init__(self, root_directory, field_properties=None):
        self.root = root_directory
        self.term_plists = dict()
        self.field_keys = dict()
        self.field_properties = field_properties
        self.documents_number = 0
        self.terms_number = 0
        self.barrels_ldb = None
        self.cache_size = 0
        if field_properties is not None:
            i = 0
            for field_name, _ in self.field_properties:
                self.field_keys[field_name] = i
                i += 1

    def init_index(self):
        if not os.path.exists(self.root):
            os.mkdir(self.root)
        if not os.path.exists(os.path.join(self.root, self.BARRELS_DIR)):
            os.mkdir(os.path.join(self.root, self.BARRELS_DIR))
        self.dump_meta()

    def dump_meta(self):
        meta_file = open(os.path.join(self.root, self.META_FILE), "w")
        meta_file.write(self.dumps_meta())
        meta_file.close()

    def load_meta(self):
        meta_file = open(os.path.join(self.root, self.META_FILE), "r")
        meta_str = meta_file.read()
        meta_file.close()
        self.loads_meta(meta_str)

    def dumps_meta(self):
        return json.dumps({
            "documents_number": self.documents_number,
            "terms_number": self.terms_number,
            "fields": [{"name": p[0], "type": dtype_to_name(p[1])} for p in self.field_properties]
        }, indent=8)

    def loads_meta(self, meta_str):
        meta = json.loads(meta_str)
        self.documents_number = meta["documents_number"]
        self.terms_number = meta["terms_number"]
        self.field_properties = [(p["name"], name_to_dtype(p["type"])) for p in meta["fields"]]
        i = 0
        for field_name, _ in self.field_properties:
            self.field_keys[field_name] = i
            i += 1

    def open(self):
        if self.barrels_ldb is not None:
            raise Exception("Index is already opened.")
        self.load_meta()
        self.barrels_ldb = leveldb.LevelDB(os.path.join(self.root, self.BARRELS_DIR))

    def load(self):
        logging.info("Loading posting lists to memory.")
        total_plists = 0
        total_bytes = 0
        term_plists = dict()
        properties_number = len(self.field_properties)
        for field_key, field_value in self.barrels_ldb.RangeIter():
            term_id, field_name = field_key.split(self.INDEX_KEY_SEP)
            term_id = int(term_id)
            if term_id in term_plists:
                plist = term_plists[term_id]
            else:
                plist = PostingList.create_empty(properties_number)
                term_plists[term_id] = plist
            field_index = self.field_keys[field_name]
            plist.set_field(field_index, field_value, self.field_properties[field_index][1])
            total_bytes += len(field_value)
            total_plists += 1
        self.term_plists = [None] * len(term_plists)
        for plist_index, plist in term_plists.iteritems():
            self.term_plists[plist_index] = plist
        logging.info("Loaded %d (%d) posting lists." % (total_plists, len(self.term_plists)))
        logging.info("Loaded %d MB." % (total_bytes / (1024 * 1024)))
        gc.collect()

    def load_plist(self, term_id):
        plist = PostingList.create_empty(len(self.field_properties))
        for i in xrange(len(self.field_properties)):
            key = str(term_id) + self.INDEX_KEY_SEP + str(i)
            field_blob = self.barrels_ldb.Get(key)
            plist.set_field(i, field_blob, self.field_properties[i][1])
            logging.debug("Loaded %d field for %d term (%d bytes)" % (i, term_id, len(field_blob)))
        return plist

    def load_plists(self, term_ids, old_plists=None, max_cache_size=1024):
        plists = dict()
        if old_plists is None:
            old_plists = dict()
        not_loaded = []
        for term_id in term_ids:
            if term_id in old_plists:
                plists[term_id] = old_plists[term_id]
                del old_plists[term_id]
            else:
                not_loaded.append(term_id)
        for key in old_plists.keys():
            if len(old_plists) <= max_cache_size:
                break
            del old_plists[key]
        gc.collect()
        for term_id in not_loaded:
            plists[term_id] = self.load_plist(term_id)
        return plists

    def get_plists(self, term_ids):
        barrels = dict()
        for term_id in term_ids:
            barrels[term_id] = self.term_plists[term_id]
        return barrels

    def dump_and_merge(self):
        if self.barrels_ldb is None:
            raise Exception("Index is not opened.")

        m = len(self.field_properties)
        batch = leveldb.WriteBatch()
        logging.info("Storage: merging index with new batch [%d x %d posting lists]." % (
            len(self.term_plists),
            len(self.field_properties),
        ))

        for plist_key, plist in self.term_plists.iteritems():

            prime_key = str(plist_key) + self.INDEX_KEY_SEP + "0"

            try:
                prime_key_val = self.barrels_ldb.Get(prime_key)
                key_exist = prime_key_val is not None
            except KeyError:
                key_exist = False

            for j in xrange(m):
                key = str(plist_key) + self.INDEX_KEY_SEP + str(j)
                if key_exist:
                    old_value = np.fromstring(self.barrels_ldb.Get(prime_key), self.field_properties[j][1])
                    add_value = plist.fields[j][:plist.size]
                    new_value = np.concatenate((old_value, add_value))
                else:
                    #old_value = np.array([], self.field_properties[j][1])
                    #add_value = plist.fields[j][:plist.size]
                    #new_value = add_value
                    new_value = plist.fields[j][:plist.size]
                batch.Put(key, new_value.tostring())

            #if i % self.BATCH_SZ == 0:
            #    self.barrels_ldb.Write(batch, sync=False)
            #    batch = leveldb.WriteBatch()

            #i += 1

        self.barrels_ldb.Write(batch, sync=False)
        self.cache_size = 0
        self.term_plists = dict()
        gc.collect()

        logging.info("Cache has been dump")

    def close(self):
        if self.barrels_ldb is None:
            raise Exception("Index is not opened.")
        self.barrels_ldb = None
        self.dump_meta()

    def add_to_index(self, document_id, index_entry):
        for vector in index_entry.property_vectors():
            term_id = vector[0]
            vector[0] = document_id
            plist = self.term_plists.get(term_id)
            if plist is None:
                plist = PostingList.create_and_init(self.field_properties)
                self.term_plists[term_id] = plist
            self.terms_number += 1
            self.cache_size += 1
            plist.add(vector)
        if self.cache_size >= self.CACHE_SZ:
            self.dump_and_merge()
        self.documents_number += 1