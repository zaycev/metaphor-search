#!/usr/bin/env python
# coding: utf-8

# Author: Vladimir M. Zaytsev <zaytsev@usc.edu>

import sys
import json

_, ifile, ofile, k = sys.argv

ifile = open(ifile, "rb")
ofile = open(ofile, "wb")
k = int(k)

data = json.load(ifile)

m = data[0]
tuples = []



for m in data:
    t = m["metaphorAnnotationRecords"]["annotationMappings"]["target"]
    s = m["metaphorAnnotationRecords"]["annotationMappings"]["source"]
    sent = m["metaphorAnnotationRecords"]["context"]
    tuples.append((t, s, sent))



d = {}
for t, s, sent in tuples:
    if (t,s) not in d:
        d[(t,s)] = [sent]
    elif len(d[(t, s)]) < k or k == -1:
        d[(t,s)].append(sent)



for (t, s), sents in d.iteritems():
    for sent in sents:
        ofile.write("%s-%s\t%s\n" % (t, s, sent))


ofile.close()
ifile.close()
