#!/usr/bin/env python
# coding: utf-8

# Copyright (C) USC Information Sciences Institute
# Author: Vladimir M. Zaytsev <zaytsev@usc.edu>
# URL: <http://nlg.isi.edu/>
# For more information, see README.md
# For license information, see LICENSE

import re
import sys
import glob
import logging
import threading
import multiprocessing


from hugin.lfparser import MetaphorAdpLFReader, POS


class SourceTargetSearcher(object):

    def __init__(self, query):
        self.domains = []
        self.query = query
        self.compile_patterns()

    def compile_patterns(self):
        for domain in self.query:
            label = domain.label
            source_w = domain.source_terms
            target_w = domain.target_terms
            source_p = [(i, self.__compile(w)) for i, w in enumerate(source_w)]
            target_p = [(i, self.__compile(w)) for i, w in enumerate(target_w)]
            source_w = [(i, w.split(" ")) for i, w in enumerate(source_w)]
            target_w = [(i, w.split(" ")) for i, w in enumerate(target_w)]
            self.domains.append((label, [
                domain.source_terms,
                source_p,
                source_w,
                domain.target_terms,
                target_p,
                target_w,
            ]))

    @staticmethod
    def __compile(pattern_str):
        words = pattern_str.split(" ")
        return [re.compile(".*\s+" + word + "\s+.*") for word in words]

    def __find_occurances(self, sent, words):
        match = []
        for w in words:
            w_match = (w, [])
            for pred in sent:
                if pred.lemma == w.decode("utf-8"):
                    w_match[1].append(pred)
            match.append(w_match)
        if all(map(lambda w_match: len(w_match[1]) > 0, match)):
            return match
        return None

    def __p_connected(self, sent, p1, p2, visited=set(), search_depth=4):
        # check if connected by args
        visited.add(id(p1))
        for arg1 in p1.args:
            for arg2 in p2.args:
                if arg1 == arg2:
                    return arg1
                for p in sent:
                    if p.pos.pos == POS.NONE:
                        if arg1 in p.args and arg2 in p.args:
                            return p
        for arg in p1.args:
            for p in sent.index.find(arg=arg):
                if id(p) not in visited:
                    result = self.__p_connected(sent, p, p2, visited, search_depth - 1)
                    if result is not False:
                        return result
        return False

    def __o_connected(self, sent, occs_1, occs_2):
        for w, occs1 in occs_1:
            for w, occs2 in occs_2:
                for p1 in occs1:
                    for p2 in occs2:
                        connection = self.__p_connected(sent, p1, p2)
                        if connection:
                            return p1, p2, connection
        return False

    def find_matches(self, sent):
        matches = []
        text = " ".join(sent.lemmas())
        for label, [source, source_p, _, target, target_p, _] in self.domains:
            source_i = None
            target_i = None
            for i, ps in source_p:
                full_match = True
                for p in ps:
                    if p.match(text) is None:
                        full_match = False
                        break
                if full_match:
                    source_i = i
                    break

            for i, ps in target_p:
                full_match = True
                for p in ps:
                    if p.match(text) is None:
                        full_match = False
                        break
                if full_match:
                    target_i = i
                    break

            if source_i is not None and target_i is not None:
                matches.append((label, source[source_i], target[target_i]))

        return matches

    def find_dep_matches(self, sent):
        matches = []
        for label, [source, _, source_w, target, _, target_w] in self.domains:
            for i, s_words in source_w:
                s_occ = self.__find_occurances(sent, s_words)
                for j, t_words in target_w:
                    t_occ = self.__find_occurances(sent, t_words)
                    if s_occ and t_occ and self.__o_connected(sent, s_occ, t_occ):
                        matches.append((label, source[i], target[j]))
        return matches


class ParallelReader(object):
    STOP = -1

    def __init__(self, dir_path, o_queue, n_jobs=2, max_sz=4096):
        self.file_list = glob.glob(dir_path)
        self.i_queue = multiprocessing.Queue(max_sz)
        self.o_queue = o_queue
        self.procs = []
        self.n_jobs = n_jobs
        target = ParallelReader.parse_lf_lines
        for i in xrange(self.n_jobs):
            proc = multiprocessing.Process(args=(self.i_queue, self.o_queue), target=target)
            self.procs.append(proc)
        logging.info("INITIALIZING READERS")

    def start(self):
        logging.info("START READERS")
        for p in self.procs:
            p.start()

    def fill(self):
        logging.info("FILLING READING QUEUE")
        for fl in self.file_list:
            self.i_queue.put(fl, block=True)
        for i in xrange(self.n_jobs * 2):
            self.i_queue.put(ParallelReader.STOP)

    def join(self):
        logging.info("JOINING READERS POOL")
        for p in self.procs:
            p.join()


    @staticmethod
    def parse_lf_lines(i_file_queue, o_queue):
        logging.info("READER LAUNCHED")
        while True:
            item = i_file_queue.get(block=True)
            if item == ParallelReader.STOP:
                logging.info("STOPPING READER")
                return
            else:
                logging.info("START READING %s FILE" % item)
                fl_file = open(item, "r")
                reader = MetaphorAdpLFReader(fl_file)
                for sent in reader.i_sentences():
                    o_queue.put(sent, block=True)
                logging.info("READING DONE %s FILE" % item)


class ParallelSearcher(object):
    STOP = -1

    def __init__(self, i_queue, o_queue, query, n_jobs=4):
        self.i_queue = i_queue
        self.o_queue = o_queue
        self.n_jobs = n_jobs
        target = ParallelSearcher.process_sentences
        proc_args = (self.i_queue, self.o_queue, query)
        self.procs = [multiprocessing.Process(target=target, args=proc_args) for _ in xrange(n_jobs)]
        logging.info("PARALLEL SEARCHER INITIALIZED")

    @staticmethod
    def process_sentences(i_queue, o_queue, query):
        logging.info("SEARCHER LAUNCHED")
        searcher = SourceTargetSearcher(query)
        while True:
            item = i_queue.get(block=True)
            if item == ParallelSearcher.STOP:
                logging.info("STOP SEARCHER")
                return
            else:
                sent = item
                matches = searcher.find_dep_matches(sent)
                o_queue.put((sent, matches), block=True)

    def start(self):
        logging.info("START SEARCHERS")
        for p in self.procs:
            p.start()

    def join(self):
        logging.info("JOINING SEARCHERS")
        for p in self.procs:
            p.join()

    def stop(self):
        logging.info("STOPPING")
        for i in xrange(self.n_jobs * 2):
            self.i_queue.put(ParallelSearcher.STOP)


class SentenceCrawler(object):

    def __init__(self, input_dir_path, o_file, query, max_sz=8192, n_jobs=(1, 1)):
        self.n_jobs = n_jobs
        self.sent_queue = multiprocessing.Queue(max_sz)
        self.result_queue = multiprocessing.Queue(max_sz)
        self.reader = ParallelReader(input_dir_path, self.sent_queue, n_jobs=n_jobs[0])
        self.searcher = ParallelSearcher(self.sent_queue, self.result_queue, query, n_jobs=n_jobs[1])
        self.output_writer = threading.Thread(target=SentenceCrawler.write_output, args=(self.result_queue, o_file))

    @staticmethod
    def write_output(i_queue, o_file):
        while True:
            item = i_queue.get(block=True)
            if item == -1:
                return
            else:
                sent, matches = item
                for match in matches:
                    o_file.write(SentenceCrawler.format_output(sent, match))

    @staticmethod
    def format_output(sent, match):
        label, source, target = match
        sid = sent.sid
        text = sent.raw_text
        o_str = "[id:%d, domain:%s, source:%s, target:%s] \n %s\n" % (
            sid,
            label,
            source,
            target,
            text.encode("utf-8")
        )
        return o_str

    def run(self, o_file=sys.stdout):
        self.reader.start()
        self.searcher.start()
        self.output_writer.start()
        self.reader.fill()
        self.reader.join()
        self.searcher.stop()
        self.searcher.join()
        self.result_queue.put(-1, block=True)
        self.output_writer.join()
        logging.info("ALL DONE")
