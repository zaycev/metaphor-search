#!/usr/bin/env python
# coding: utf-8

# Copyright (C) USC Information Sciences Institute
# Author: Vladimir M. Zaytsev <zaytsev@usc.edu>
# URL: <http://nlg.isi.edu/>
# For more information, see README.md
# For license information, see LICENSE

import unidecode


def transliterate(string):
    if isinstance(string, unicode):
        return unidecode.unidecode(string)
    return unidecode.unidecode(string.decode("utf-8"))
