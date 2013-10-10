#!/usr/bin/env python
# coding: utf-8

# Copyright (C) USC Information Sciences Institute
# Author: Vladimir M. Zaytsev <zaytsev@usc.edu>
# URL: <http://nlg.isi.edu/>
# For more information, see README.md
# For license information, see LICENSE

import json


class Domain(object):

    def __init__(self, label, target_terms, source_terms):
        self.label = label.encode("utf-8")
        self.target_terms = [t.encode("utf-8").replace(" ", "&") for t in target_terms]
        self.source_terms = [t.encode("utf-8").replace(" ", "&") for t in source_terms]


class DomainSearchQuery(object):

    def __init__(self, domains):
        self.domains = domains

    @staticmethod
    def fromstring(json_string):
        query_dict = json.loads(json_string)
        domains = []
        for domain_node in query_dict["query"]:
            label = domain_node["label"]
            target_terms = domain_node["target"]
            source_terms = domain_node["source"]
            domains.append(Domain(label, target_terms, source_terms))
        return DomainSearchQuery(domains)

    def __iter__(self):
        for domain in self.domains:
            yield domain