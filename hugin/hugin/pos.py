#!/usr/bin/env python
# coding: utf-8

# Copyright (C) USC Information Sciences Institute
# Author: Vladimir M. Zaytsev <zaytsev@usc.edu>
# URL: <http://nlg.isi.edu/>
# For more information, see README.md
# For license information, see LICENSE


class POS(object):

    NONE = 0x00
    VB = 0x01
    NN = 0x02
    ADJ = 0x03
    RB = 0x04
    PREP = 0x05
    PR = 0x06
    ANY = 0x07


class Pos(object):

    def __init__(self, pos_tag=None):
        self.pos = POS.NONE
        if pos_tag == "vb" or pos_tag == "v":
            self.vb = True
            self.pos = POS.VB
        else:
            self.vb = False
        if pos_tag == "nn" or pos_tag == "n":
            self.nn = True
            self.pos = POS.NN
        else:
            self.nn = False
        if pos_tag == "adj" or pos_tag == "a":
            self.adj = True
            self.pos = POS.ADJ
        else:
            self.adj = False
        if pos_tag == "rb" or pos_tag == "r":
            self.rb = True
            self.pos = POS.RB
        else:
            self.rb = False
        if pos_tag == "in" or pos_tag == "p":
            self.prep = True
            self.pos = POS.PREP
        else:
            self.prep = False
        if pos_tag == "pr":
            self.pr = True
            self.pos = POS.PR
        else:
            self.pr = False

    @staticmethod
    def fromenum(enum):
        if enum == POS.VB:
            return Pos("vb")
        if enum == POS.NN:
            return Pos("nn")
        if enum == POS.ADJ:
            return Pos("adj")
        if enum == POS.RB:
            return Pos("rb")
        if enum == POS.PREP:
            return Pos("in")
        if enum == POS.PR:
            return Pos("pr")
        return Pos(None)

    def __str__(self):
        if self.vb:
            return "VB"
        if self.nn:
            return "NN"
        if self.adj:
            return "ADJ"
        if self.rb:
            return "RB"
        if self.prep:
            return "PREP"
        if self.pr:
            return "PR"
        return "<NONE-POS>"

    def __int__(self):
        return self.pos

    def __repr__(self):
        return self.__str__()


POS_ID_NAME_MAP = {
    POS.ANY:    "ANY",
    POS.NONE:   "NONE",
    POS.VB:     "VB",
    POS.NN:     "NN",
    POS.ADJ:    "ADJ",
    POS.RB:     "RB",
    POS.PREP:   "PREP",
    POS.PR:     "PR",
}

POS_NAME_ID_MAP = {pos_name:pos_id
                   for pos_id, pos_name
                   in POS_ID_NAME_MAP.iteritems()}

POS_NAMES = [pos_name for pos_name in POS_ID_NAME_MAP.itervalues() if
             pos_name != POS_ID_NAME_MAP[POS.NONE] and
             pos_name != POS_ID_NAME_MAP[POS.ANY]]