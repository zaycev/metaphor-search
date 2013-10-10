# coding: utf-8
# Author: Vladimir M. Zaytsev <zaytsev@usc.edu>


class Searcher(object):

    def __init__(self, index):
        self.index = index

    def find(self, query, ret_field):

        intersect_lists = []
        ret_field_id = self.index.field_keys[ret_field]

        for term_id, constraints in query:

            plist = self.index.load_plist(term_id)

            if len(constraints) == 0:
                intersect_lists.append(plist.fields[ret_field_id])
                continue

            candidates = []
            for i in xrange(0, len(plist.fields[0])):
                candidate_is_ok = True

                for c_name, constraint in constraints:
                    c_field_id = self.index.field_keys[c_name]
                    if not constraint(plist.fields[c_field_id][i]):
                        candidate_is_ok = False
                        break

                candidate = plist.fields[ret_field_id][i]

                if candidate_is_ok:
                    candidates.append(candidate)

            if len(candidates) == 0:
                return []
            intersect_lists.append(candidates)

        last_candidates = set(intersect_lists[0])

        for i in xrange(1, len(intersect_lists)):
            new_candidates = set()
            for j in xrange(len(intersect_lists[i])):
                if intersect_lists[i][j] in last_candidates:
                    new_candidates.add(intersect_lists[i][j])
            last_candidates = new_candidates
        return last_candidates