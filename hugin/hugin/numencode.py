#!/usr/bin/env python
# coding: utf-8

# Copyright (C) USC Information Sciences Institute
# Author: Vladimir M. Zaytsev <zaytsev@usc.edu>
# URL: <http://nlg.isi.edu/>
# For more information, see README.md
# For license information, see LICENSE

import array
import string


ALPHABET = string.ascii_letters
ALPHABET_REVERSE = dict((c, i) for (i, c) in enumerate(ALPHABET))
BASE = len(ALPHABET)
LONG_SIZE = 8


def encode_uint(uint_val):
    s = []
    while True:
        uint_val, r = divmod(uint_val, BASE)
        s.append(ALPHABET[r])
        if uint_val == 0:
            break
    return ''.join(reversed(s))


def decode_uint(uint_str):
    n = 0
    for c in uint_str:
        n = n * BASE + ALPHABET_REVERSE[c]
    return n


def delta_encode(sorted_sequence):
    i = len(sorted_sequence) - 1
    while i > 0:
        sorted_sequence[i] -= sorted_sequence[i - 1]
        i -= 1


def delta_decode(delta_sequence):
    i = 1
    while i < len(delta_sequence):
        delta_sequence[i] += delta_sequence[i - 1]
        i += 1


def encode_plist(plist):
    tid_arr = array.array("l", [0] * len(plist))
    pos_arr = array.array("B", [0] * len(plist))
    i = 0
    while i < len(plist):
        tid_arr[i] = plist[i][0]
        pos_arr[i] = plist[i][1]
        i += 1
    delta_encode(tid_arr)
    sz = array.array("L", [len(plist)])
    return sz.tostring() + pos_arr.tostring() + tid_arr.tostring()


def decode_plist(plist_data):
    sz = array.array("L")
    sz.fromstring(plist_data[:LONG_SIZE])
    sz = sz[0]
    tid_arr = array.array("l")
    pos_arr = array.array("B")
    pos_arr.fromstring(plist_data[LONG_SIZE:(LONG_SIZE + sz)])
    tid_arr.fromstring(plist_data[(LONG_SIZE + sz):])
    delta_decode(tid_arr)
    return zip(tid_arr, pos_arr)


def update_plist(plist_data, new_plist):
    sz = array.array("L")
    sz.fromstring(plist_data[:LONG_SIZE])
    sz = sz[0]
    tid_arr = array.array("l")
    pos_arr = array.array("B")
    pos_arr.fromstring(plist_data[LONG_SIZE:(LONG_SIZE + sz)])
    tid_arr.fromstring(plist_data[(LONG_SIZE + sz):])
    delta_decode(tid_arr)
    for tr_id, ag_pos in new_plist:
        tid_arr.append(tr_id)
        pos_arr.append(ag_pos)
    delta_encode(tid_arr)
    sz = array.array("L", [sz + len(new_plist)])
    return sz.tostring() + pos_arr.tostring() + tid_arr.tostring()


def encode_1d_plist(plist):
    tid_arr = array.array("l", [0] * len(plist))
    i = 0
    while i < len(plist):
        tid_arr[i] = plist[i]
        i += 1
    delta_encode(tid_arr)
    return tid_arr.tostring()


def decode_1d_plist(plist_data):
    tid_arr = array.array("l")
    tid_arr.fromstring(plist_data)
    delta_decode(tid_arr)
    return tid_arr


def update_1d_plist(plist_data, new_plist):
    tid_arr = array.array("l")
    tid_arr.fromstring(plist_data)
    delta_decode(tid_arr)
    for tr_id in new_plist:
        tid_arr.append(tr_id)
    delta_encode(tid_arr)
    return tid_arr.tostring()