#!/usr/bin/env python
# coding: utf-8

# Author: Vladimir M. Zaytsev <zaytsev@usc.edu>

import random
import unittest

import hugin.pos
import hugin.relsearch
import metaphor.processing

TESTS_NUM = 1000


class TestTriplet(unittest.TestCase):

    def test_init(self):
        for rel in hugin.relsearch.RELATION_NAMES:
            for pos in hugin.pos.POS_NAMES:
                triplet = metaphor.processing.Triplet(0, rel, [("term", pos)], 1)
                self.assertIsNotNone(triplet)

    def test_tostring(self):
        for _ in xrange(0, TESTS_NUM):
            K = 3
            argument_pos = random.sample(hugin.pos.POS_NAMES, K)
            arguments = [("some_term", pos) for pos in argument_pos]
            arguments += [None]
            frequency = random.randint(0, 0xFFFFFFFF)
            rel_type = random.choice(hugin.relsearch.RELATION_NAMES)
            triplet_id = random.randint(0, 0xFFFFFFFF)
            #print rel_type
            triplet = metaphor.processing.Triplet(triplet_id, rel_type, arguments, frequency)
            tstring = triplet.tostring()
            copy_triplet = metaphor.processing.Triplet(triplet_id)
            copy_triplet.fromstring(tstring)
            self.assertEqual(tstring, copy_triplet.tostring())

if __name__ == "__main__":
        unittest.main()
