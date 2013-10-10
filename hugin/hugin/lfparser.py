#!/usr/bin/env python
# coding: utf-8

# Copyright (C) USC Information Sciences Institute
# Author: Vladimir M. Zaytsev <zaytsev@usc.edu>
# URL: <http://nlg.isi.edu/>
# For more information, see README.md
# For license information, see LICENSE

import logging

from hugin.pos import POS
from hugin.pos import Pos


class PredicateArguments(object):

    def __init__(self, arg_list):
        self.arg_list = [False] * len(arg_list)
        for i, arg in enumerate(arg_list):
            if arg and arg[0] != "u":
                self.arg_list[i] = arg

    @property
    def first(self):
        if len(self.arg_list) > 0:
            return self.arg_list[0]
        return False

    @property
    def second(self):
        if len(self.arg_list) > 1:
            return self.arg_list[1]
        return False

    @property
    def third(self):
        if len(self.arg_list) > 2:
            return self.arg_list[2]
        return False

    @property
    def fourth(self):
        if len(self.arg_list) > 3:
            return self.arg_list[3]
        return False

    def __iter__(self):
        for arg in self.arg_list:
            yield arg


class Predicate(object):

    def __init__(self, pid=None, lemma=None, pos=None, args=None, extra=None, none=False):
        self.none = none
        if not none:
            self.pid = pid
            self.lemma = lemma
            self.pos = Pos(pos)
            self.args = PredicateArguments(args)
            self.extra = extra
        else:
            self.pid = None
            self.lemma = None
            self.pos = None
            self.args = None
            self.extra = None

    def lemma_pos(self):
        if self.none:
            return "<NONE>"
        return u"%s-%s" % (self.lemma, self.pos)

    @staticmethod
    def fromstr(line):
        result = line.split(":")
        if len(result) != 2:
            pid = result[0]
            other = result[1:len(result)]
            other = "".join(other)
        else:
            pid, other = line.split(":")
        result = other.split("-")
        if len(result) != 2:
            other = result[-1]
            lemma = "-".join(result[0:len(result) - 1])
        else:
            lemma, other = result
        pos, arg_line = other.split("(")
        arg_line = arg_line[0:(len(arg_line) - 1)]
        args = arg_line.split(",")
        return Predicate(pid, lemma, pos, args)

    @staticmethod
    def efromstr(line):
        result = line.split("(")
        if result == 2:
            extra, arg_line = result
        else:
            extra = result[0:(len(result) - 1)]
            arg_line = result[-1]
        arg_line = arg_line[0:(len(arg_line) - 1)]
        args = arg_line.split(",")
        return Predicate(-1, None, None, args, extra[0])

    def __eq__(self, other):
        if self.lemma is None:
            return False
        if other.lemma is None:
            return False
        return self.lemma == other.lemma

    def __hash__(self):
        return self.lemma.__hash__()

    def __repr__(self):
        if self.extra is None:
            predicate_str = u"%s-%s(%s)" % (
                self.lemma,
                self.pos,
                u", ".join([str(arg) for arg in self.args])
            )
        else:
            predicate_str = u"%s(%s)" % (
                self.extra,
                u", ".join([str(arg) for arg in self.args])
            )
        return predicate_str.encode("utf-8")


class PredicateSet(object):

    def __init__(self, predicates, pos, max_sequence=4):
        self.predicates = list(set(predicates)) if len(predicates) <= max_sequence else []
        self.pos = Pos.fromenum(pos)

    def lemmas(self):
        return [pred.lemma for pred in self.predicates]

    def lemma_pos(self):
        if len(self.predicates) > 0:
            lemmas = sorted([pred.lemma for pred in self.predicates])
            lemmas = "&&".join(lemmas)
            return u"%s-%r" % (lemmas, self.pos)
        return "<NONE>"

    def __cmp__(self, other):
        set1 = set(other.lemmas())
        set2 = set(self.lemmas())
        if set1 == set2:
            return 0
        return 1

    def __eq__(self, other):
        set1 = set(other.lemmas())
        set2 = set(self.lemmas())
        return set1 == set2

    def __int__(self):
        return len(self.predicates)

    def __str__(self):
        if list(self.predicates) == 0:
            return "<NONE>"
        else:
            set_str = u"<PredicateSet(%s)>" % self.lemma_pos()
        return set_str.encode("utf-8")

    def __len__(self):
        return len(self.predicates)

    def __repr__(self):
        return self.__str__()


class SentenceIndex(object):

    def __init__(self, sentence):

        self.i_dic_arg = dict()
        self.i_dic_arg_first = dict()
        self.i_dic_arg_second = dict()
        self.i_dic_arg_third = dict()
        self.i_dic_arg_fourth = dict()
        self.i_dic_extra = dict()
        self.sentence = sentence

        for pred in sentence:
            for arg in pred.args:
                if arg is not None:
                    if arg in self.i_dic_arg:
                        self.i_dic_arg[arg].append(pred)
                    else:
                        self.i_dic_arg[arg] = [pred]
            if pred.extra:
                if pred.extra in self.i_dic_extra:
                    self.i_dic_extra[pred.extra].append(pred)
                else:
                    self.i_dic_extra[pred.extra] = [pred]
            if pred.args.first:
                if pred.args.first in self.i_dic_arg_first:
                    self.i_dic_arg_first[pred.args.first].append(pred)
                else:
                    self.i_dic_arg_first[pred.args.first] = [pred]
            if pred.args.second:
                if pred.args.second in self.i_dic_arg_second:
                    self.i_dic_arg_second[pred.args.second].append(pred)
                else:
                    self.i_dic_arg_second[pred.args.second] = [pred]
            if pred.args.third:
                if pred.args.third in self.i_dic_arg_third:
                    self.i_dic_arg_third[pred.args.third].append(pred)
                else:
                    self.i_dic_arg_third[pred.args.third] = [pred]
            if pred.args.fourth:
                if pred.args.fourth in self.i_dic_arg_fourth:
                    self.i_dic_arg_fourth[pred.args.fourth].append(pred)
                else:
                    self.i_dic_arg_fourth[pred.args.fourth] = [pred]

    def find(self, first=None, second=None, third=None, fourth=None, pos=None, arg=None, extra=None, return_set=False):
        predicate_lists = []
        if arg is not None:
            predicate_lists.append(self.i_dic_arg.get(arg, []))
        if extra is not None:
            predicate_lists.append(self.i_dic_extra.get(extra, []))
        if first is not None:
            predicate_lists.append(self.i_dic_arg_first.get(first, []))
        if second is not None:
            predicate_lists.append(self.i_dic_arg_second.get(second, []))
        if third is not None:
            predicate_lists.append(self.i_dic_arg_third.get(third, []))
        if fourth is not None:
            predicate_lists.append(self.i_dic_arg_fourth.get(fourth, []))
        if pos is not None and pos is not POS.NONE:
            predicate_lists.append(filter(lambda p: p.pos.pos == pos, self.sentence))
        if len(predicate_lists) == 1:
            if return_set and pos:
                return PredicateSet(predicate_lists[0], pos)
            return predicate_lists[0]
        else:
            list1 = predicate_lists.pop()
            matched = []
            for e in list1:
                in_intersection = True
                for l in predicate_lists:
                    if e not in l:
                        in_intersection = False
                        break
                if in_intersection:
                    matched.append(e)
            if return_set and pos is not None:
                return PredicateSet(matched, pos)
            return matched


class Sentence(object):

    def __init__(self, sid, predicates, line=None, raw_text=None):
        self.line = line
        self.predicates = predicates
        self.sid = sid
        self.index = SentenceIndex(self)
        self.raw_text = raw_text

    def lemmas(self):
        lemmas = []
        for p in self.predicates:
            if p.lemma is not None:
                lemmas.append(p.lemma)
        return lemmas

    @staticmethod
    def from_lf_line(lf_line_index, lf_line):
        predicates = []
        
        lf_line = lf_line.replace(" & ", "&")
        lf_line = lf_line.replace("((", "(")
        lf_line = lf_line.replace("))", ")")
        
        predicate_str = lf_line.split("&")
        predicate_str = filter(lambda t: t != "&", predicate_str)
        for i, p_str in enumerate(predicate_str):
            try:
                if p_str[0] == "[":
                    predicate = Predicate.fromstr(p_str)
                    if predicate.lemma and predicate.pos.pos:
                        predicates.append(predicate)
                else:
                    predicate = Predicate.efromstr(p_str)
                    if len(predicate.extra) > 0:
                        predicates.append(predicate)
            except Exception:
                try:
                    logging.error("Error while parsing line: %s" % lf_line)
                except Exception:
                    pass

        return Sentence(lf_line_index, predicates, lf_line)

    def __iter__(self):
        for pred in self.predicates:
            yield pred

    def __len__(self):
        return len(self.predicates)


class MetaphorAdpLFReader(object):

    def __init__(self, lf_file):
        self.lf_file = lf_file

    def i_sentences(self):
        i = 0
        text = None
        for line in self.lf_file:
            line = line.decode("utf-8")
            if line[0] == "%":
                if len(line) >= 3 and line[0:3] == "%%%":
                    text = line[4:len(line)]
                else:
                    text = line[2:len(line)]
            elif len(line) >= 3 and line[0:3] == "id(":
                continue
            elif line[0].isdigit():
                continue
            elif len(line) > 1:
                sentence = Sentence.from_lf_line(i, line)
                sentence.raw_text = text
                i += 1
                yield sentence
            else:
                continue
