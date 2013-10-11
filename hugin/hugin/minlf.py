#!/usr/bin/env python
# coding: utf-8

# Copyright (C) USC Information Sciences Institute
# Author: Vladimir M. Zaytsev <zaytsev@usc.edu>
# URL: <http://nlg.isi.edu/>
# For more information, see README.md
# For license information, see LICENSE

import re
import logging


class MinLFSParser(object):
    LF_COMMENT_PRT = re.compile("%+\s*(.+)")
    LF_TERM_PRT = re.compile("((\[.+?\]\:)([^ .]+?)\-[a-z]+(\([,a-z0-9]+?\))?)")
    LF_EMPTY_LINE = re.compile("^\s*$")

    def __init__(self, i_file):
        self.i_file = i_file

    def __iter__(self):
        raw_text = ""
        for line in self.i_file:
            if line.startswith("%"):
                raw_text_match = self.LF_COMMENT_PRT.findall(line)
                if len(raw_text_match) == 1:
                    raw_text = raw_text_match[0]
                else:
                    raw_text = ""
                    logging.warn("Got strange LF comment line: %s" % line)
            elif line.startswith("id(") or self.LF_EMPTY_LINE.match(line):
                continue
            else:
                terms_match = self.LF_TERM_PRT.findall(line)
                terms = [m[2] for m in terms_match] if terms_match is not None else []
                lf_line = line
                yield raw_text, lf_line, terms