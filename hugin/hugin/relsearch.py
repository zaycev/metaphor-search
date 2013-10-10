# coding: utf-8

# Copyright (C) USC Information Sciences Institute
# Author: Vladimir M. Zaytsev <zaytsev@usc.edu>
# URL: <http://nlg.isi.edu/>
# For more information, see README.md
# For license information, see LICENSE

import logging
import collections

from hugin.pos import POS


class AbsDependencyRelation(object):
    rel_name = "abstract"

    def together(self, *args):
        lemmas = ["N" if a is None else a for a in args]
        return "".join(sorted(lemmas))

    def find_matches(self, sentence):
        raise NotImplementedError()


class Triple(object):

    def __init__(self, relation, arg1=None, arg2=None, arg3=None, arg4=None, arg5=None):
        self.relation = relation
        self.arg1 = arg1
        self.arg2 = arg2
        self.arg3 = arg3
        self.arg4 = arg4
        self.arg5 = arg5

    @staticmethod
    def to_row(triple_tuple):
        relation, arg1, arg2, arg3, arg4, arg5, freq = triple_tuple
        return "%s, %s, %s, %s, %s, %s, %d" % (relation, arg1, arg2, arg3, arg4, arg5, freq,)

    def pack(self):
        return "<^>".join((
            self.relation,
            self.arg1.lemma_pos() if self.arg1 is not None else "<->",
            self.arg2.lemma_pos() if self.arg2 is not None else "<->",
            self.arg3.lemma_pos() if self.arg3 is not None else "<->",
            self.arg4.lemma_pos() if self.arg4 is not None else "<->",
            self.arg5.lemma_pos() if self.arg5 is not None else "<->",
        ))

    @staticmethod
    def unpack(string):
        return string.split("<^>")

    def __repr__(self):
        return "Triple(%s, %s, %s, %s, %s, %s)" % (
            self.relation,
            self.arg1.lemma_pos() if self.arg1 is not None else "<->",
            self.arg2.lemma_pos() if self.arg2 is not None else "<->",
            self.arg3.lemma_pos() if self.arg3 is not None else "<->",
            self.arg4.lemma_pos() if self.arg4 is not None else "<->",
            self.arg5.lemma_pos() if self.arg5 is not None else "<->",
        )


##################################
#                                #
#       VERB RELATIONS           #
#                                #
##################################


class DepVerb_SubjVerbDirobj(AbsDependencyRelation):
    """
    Example:
    subj_verb_dirobj([noun*],verb,[noun+]) ("John reads a book")
    """
    rel_name = "subj_verb_dirobj"

    def find_matches(self, sentence):
        matches = []
        for verb in sentence.index.find(pos=POS.VB):
            subj = sentence.index.find(second=verb.args.second, pos=POS.NN, return_set=True)
            dirobj = sentence.index.find(second=verb.args.third, pos=POS.NN, return_set=True)
            if dirobj and subj != dirobj:
                matches.append(Triple(self.rel_name, subj, verb, dirobj))
        return matches


class DepVerb_SubjVerbIndirobj(AbsDependencyRelation):
    """
    Example:
    subj_verb_indirobj([noun*],verb,[noun+]) ("John gives to Mary")
    """
    rel_name = "subj_verb_indirobj"

    def find_matches(self, sentence):
        matches = []
        for verb in sentence.index.find(pos=POS.VB):
            if verb.args.fourth:
                subj = sentence.index.find(second=verb.args.second, pos=POS.NN, return_set=True)
                indirobj = sentence.index.find(second=verb.args.fourth, pos=POS.NN, return_set=True)
                if indirobj and subj != indirobj:
                    matches.append(Triple(self.rel_name, subj, verb, indirobj))
        return matches


class DepVerb_SubjVerbInstr(AbsDependencyRelation):
    """
    Example:
    subj_verb_instr([noun*],verb,[noun+]) ("Джон работает топором")
    """
    rel_name = "subj_verb_instr"

    def find_matches(self, sentence):
        matches = []
        for verb in sentence.index.find(pos=POS.VB):
            subj = sentence.index.find(second=verb.args.second, pos=POS.NN, return_set=True)
            instrs = sentence.index.find(second=verb.args.first, extra="instr")
            for instr in instrs:
                instr_noun = sentence.index.find(second=instr.args.third, pos=POS.NN, return_set=True)
                if instr_noun and subj != instr_noun:
                    matches.append(Triple(self.rel_name, subj, verb, instr_noun))
        return matches


class DepVerb_SubjVerb(AbsDependencyRelation):
    """
    Example:
    subj_verb([noun+], verb) ("John runs") // only if there is no dirobj and indirobj
    """
    rel_name = "subj_verb"

    def find_matches(self, sentence):
        matches = []
        for verb in sentence.index.find(pos=POS.VB):
            if verb.args.second and not verb.args.third and not verb.args.fourth:
                subj = sentence.index.find(second=verb.args.second, pos=POS.NN, return_set=True)
                if subj:
                    matches.append(Triple(self.rel_name, subj, verb))
        return matches


class DepVerb_PrepCompl(AbsDependencyRelation):
    """
    Example:
    subj_verb_prep_compl([noun*],verb,prep,[noun+]) ("John comes from London")
    """
    rel_name = "subj_verb_prep_compl"

    def find_matches(self, sentence):
        matches = []
        for verb in sentence.index.find(pos=POS.VB):
            if verb.args.second:
                subj = sentence.index.find(second=verb.args.second, pos=POS.NN, return_set=True)
                preps = sentence.index.find(second=verb.args.first)
                for prep in preps:
                    prep_noun = sentence.index.find(second=prep.args.third, pos=POS.NN, return_set=True)
                    if prep_noun and subj != prep_noun:
                        matches.append(Triple(self.rel_name, subj, verb, prep, prep_noun))
        return matches


class DepVerb_PrepPrepCompl(AbsDependencyRelation):
    # TODO(zaytsev@usc.edu): implement this
    """
    Example:
    subj_verb_prep_prep_compl(noun,verb,prep,prep,noun) ("John goes out of the store")
    """
    rel_name = "subj_verb_prep_compl"


class DepVerb_SubjVerbVerbPrepNoun(AbsDependencyRelation):
    """
    Example:
    subj_verb_verb_prep_noun([noun*],verb,verb,prep,[noun+]) ("John tries to go into the house")
    """
    rel_name = "subj_verb_verb_prep_noun"

    def find_matches(self, sentence):
        matches = []
        vb_pairs = []
        for verb1 in sentence.index.find(pos=POS.VB):
            if verb1.args.third:
                subj = sentence.index.find(second=verb1.args.second, pos=POS.NN, return_set=True)
                verbs2 = sentence.index.find(first=verb1.args.third, pos=POS.VB)
                verbs2 = filter(lambda p: p != verb1, verbs2)
                for verb2 in verbs2:
                    if verb1 != verb2:
                        together = self.together(verb1.lemma, verb2.lemma)
                        if together not in vb_pairs:
                            preps = sentence.index.find(second=verb2.args.first, pos=POS.PREP)
                            for prep in preps:
                                prep_noun = sentence.index.find(second=prep.args.third, pos=POS.NN, return_set=True)
                                if prep_noun and prep_noun != subj:
                                    matches.append(Triple(self.rel_name, subj, verb1, verb2, prep, prep_noun))
                                    vb_paiappend(together)
        return matches


class DepVerb_SubjVerbVerb(AbsDependencyRelation):
    """
    Example:
    subj_verb_verb([noun+],verb,verb) ("John tries to go") -> only if there is no prep attached to the second verb
    """
    rel_name = "subj_verb_verb"

    def find_matches(self, sentence):
        matches = []
        vb_pairs = []
        for verb1 in sentence.index.find(pos=POS.VB):
            if verb1.args.second:
                subject = sentence.index.find(second=verb1.args.second, pos=POS.NN, return_set=True)
                if subject:
                    verbs2 = sentence.index.find(first=verb1.args.third, pos=POS.VB)
                    verbs2 = filter(lambda p: p != verb1, verbs2)
                    for verb2 in verbs2:
                        if verb1 != verb2:
                            together = self.together(verb1.lemma, verb2.lemma)
                            if together not in vb_pairs:
                                preps = sentence.index.find(second=verb1.args.first, pos=POS.PREP)
                                if len(preps) == 0:
                                    matches.append(Triple(self.rel_name, subject, verb1, verb2))
                                    vb_paiappend(together)
        return matches


class DepVerb_NounBePrepNoun(AbsDependencyRelation):
    # TODO(zaytsev@usc.edu): implement this
    """
    Example:
    noun_be_prep_noun(noun,verb,prep,noun) ("intention to leave for money")
    """
    rel_name = "noun_be_prep_noun"


class DepVerb_NounBe(AbsDependencyRelation):
    # TODO(zaytsev@usc.edu): implement this
    """
    Example:
    noun_be(noun,verb) ("intention to leave") -> only if there is no prep attached to verb
    """
    rel_name = "noun_be"


##################################
#                                #
#        ADJ RELATIONS           #
#                                #
##################################


class DepAdj_NounBePrepNoun(AbsDependencyRelation):
    """
    Example:
    noun_adj_prep_noun(noun,adjective,prep,noun) ("The book is good for me") -> only if "for" has "good" (and not "is")
    as its arg.
    """
    rel_name = "noun_adj_prep_noun"

    def find_matches(self, sentence):
        matches = []
        for adj in sentence.index.find(pos=POS.ADJ):
            if adj.args.second:
                nouns1 = sentence.index.find(second=adj.args.second, pos=POS.NN)
                for noun1 in nouns1:
                    preps = sentence.index.find(pos=POS.PREP)
                    for prep in preps:
                        nouns2 = sentence.index.find(second=prep.args.third, pos=POS.NN)
                        for noun2 in nouns2:
                            if noun1 != noun2:
                                matches.append(Triple(self.rel_name, noun1, adj, prep, noun2))
        return matches


class DepAdj_NounAdj(AbsDependencyRelation):
    """
    Example:
    noun_adj([noun+],adjective) ("The book is good") -> only if there is no prep attached to adj as its arg.
    """
    rel_name = "noun_adj"

    def find_matches(self, sentence):
        matches = []
        for adj in sentence.index.find(pos=POS.ADJ):
            if adj.args.second:
                noun = sentence.index.find(second=adj.args.second, pos=POS.NN, return_set=True)
                preps1 = sentence.index.find(pos=POS.PREP, second=adj.args.second)
                preps2 = sentence.index.find(pos=POS.PREP, third=adj.args.second)
                if len(preps1) == 0 and len(preps2) == 0 and noun:
                    matches.append(Triple(self.rel_name, noun, adj))
        return matches


##################################
#                                #
#        ADV RELATIONS           #
#                                #
##################################


class DepAdv_NounVerbAdvPrepNoun(AbsDependencyRelation):
    # TODO(zaytsev@usc.edu): seems to be very very rare, double check this
    """
    Example:
    noun_verb_adv_prep_noun(adverb,verb) ("John runs fast for me") -> only if "for" has "fast" (and not "runs")
    as its arg.
    """
    rel_name = "noun_verb_adv_prep_noun"

    def find_matches(self, sentence):
        matches = []
        # for adv in sentence.index.find(pos=POS.RB):
        #     if adv.args.second:
        #         preps = sentence.index.find(third=adv.args.first, pos=POS.PREP)
                # print adv.lemma.encode("utf-8"), len(preps)
                # print(len(preps))
                # for prep in preps:
                #     print adv.lemma.encode("utf-8"), prep.lemma.encode("utf-8")

                # verbs = sentence.index.find(second=adv.args.second, pos=POS.VB)
                #     for verb in verbs:
                #         print verb.lemma.encode("utf-8"), adv.lemma.encode("utf-8"), prep.lemma.encode("utf-8")

                # verbs = sentence.index.find(first=adv.args.second, pos=POS.VB)
                # for verb in verbs:
                #     preps = sentence.index.find(pos=POS.PREP)
                #     for prep in preps:
                #         nouns1 = sentence.index.find(second=verb.args.second, pos=POS.NN)
                #         for noun2 in nouns2:
                #             if noun1 != noun2:
                #                 matches.append(Triple(self.rel_name, noun1, adv, prep, noun2.lemma))
        return matches


class DepAdv_VerbNounAdv(AbsDependencyRelation):
    """
    Example:
    noun_verb_adv([noun*],verb,adverb) ("John runs fast") -> only if there is no prep attached to adv
    """
    rel_name = "noun_verb_adv"

    def find_matches(self, sentence):
        matches = []
        for adv in sentence.index.find(pos=POS.RB):
            preps1 = sentence.index.find(second=adv.args.first, pos=POS.PREP)
            preps2 = sentence.index.find(third=adv.args.first, pos=POS.PREP)
            if len(preps1) == 0 and len(preps2) == 0:
                verbs = sentence.index.find(first=adv.args.second, pos=POS.VB)
                for verb in verbs:
                    subj = sentence.index.find(second=verb.args.second, pos=POS.NN, return_set=True)
                    matches.append(Triple(self.rel_name, subj, verb, adv))
        return matches


##################################
#                                #
#        NOUN RELATIONS          #
#                                #
##################################


class DepNoun_NounPrep(AbsDependencyRelation):
    """
    Example:
    nn_prep([noun+],prep,noun) ("[city]&bike for John") -> only if "for" has "bike" (and not some verb) as its arg.
    """
    rel_name = "nn_prep"

    def find_matches(self, sentence):
        matches = []
        for prep in sentence.index.find(pos=POS.PREP):
            if prep.args.second:
                comp_noun = sentence.index.find(second=prep.args.second, pos=POS.NN, return_set=True)
                if len(comp_noun) > 0:
                    pred_noun = sentence.index.find(second=prep.args.third, pos=POS.NN, return_set=True)
                    if pred_noun and comp_noun != pred_noun:
                        matches.append(Triple(self.rel_name, comp_noun, prep, pred_noun))
        return matches


class DepNoun_NounNoun(AbsDependencyRelation):
    """
    Example:
    nn(noun,noun) ("city bike") -> only if there is no prep attached to the second noun
    """
    rel_name = "nn"

    def find_matches(self, sentence):
        matches = []
        nn_pairs = []
        for noun1 in sentence.index.find(pos=POS.NN):
            preps = sentence.index.find(second=noun1.args.second, pos=POS.PREP)
            if len(preps) == 0:
                nouns2 = sentence.index.find(second=noun1.args.second, pos=POS.NN)
                nouns2 = filter(lambda p: p != noun1, nouns2)
                if len(nouns2) == 1:
                    noun2 = nouns2[0]
                    together = self.together(noun1.lemma, noun2.lemma)
                    if together not in nn_pairs:
                        if noun1.lemma != noun2.lemma:
                            matches.append(Triple(self.rel_name, noun1, noun2))
                            nn_paiappend(together)
        return matches


class DepNoun_NounNounNoun(AbsDependencyRelation):
    """
    Example:
    nnn(noun,noun,noun) ("Tzar Ivan Grozny")
    """
    rel_name = "nnn"

    def find_matches(self, sentence):
        matches = []
        nn_triples = []
        for noun1 in sentence.index.find(pos=POS.NN):
            preps = sentence.index.find(second=noun1.args.second, pos=POS.PREP)
            if len(preps) == 0:
                nouns2 = sentence.index.find(second=noun1.args.second, pos=POS.NN)
                nouns2 = filter(lambda p: p != noun1, nouns2)
                if len(nouns2) == 2:
                    noun2, noun3 = nouns2
                    together = self.together(noun1.lemma, noun2.lemma, noun3.lemma)
                    if together not in nn_triples:
                        if noun1.lemma != noun2.lemma and noun2.lemma != noun3.lemma and noun1.lemma != noun3.lemma:
                            matches.append(Triple(self.rel_name, noun1, noun2, noun3))
                            nn_triples.append(together)
        return matches


class DepNoun_NounEqualPrepNoun(AbsDependencyRelation):
    """
    Example:
    noun_equal_prep_noun(noun,noun,prep,noun) ("John is a man of heart") -> only if "of" has "man" (and not "is")
    as its arg.
    """
    rel_name = "noun_equal_prep_noun"

    def find_matches(self, sentence):
        matches = []
        nn_pairs1 = []
        nn_pairs2 = []
        nn_pairs3 = []
        for equal in sentence.index.find(extra="equal"):
            nouns1 = sentence.index.find(second=equal.args.second, pos=POS.NN)
            for noun1 in nouns1:
                nouns2 = sentence.index.find(second=equal.args.third, pos=POS.NN)
                nouns2 = filter(lambda p: p != noun1, nouns2)
                for noun2 in nouns2:
                    together1 = self.together(noun1.lemma, noun2.lemma)
                    if together1 not in nn_pairs1:
                        preps = sentence.index.find(second=noun2.args.second, pos=POS.PREP)
                        for prep in preps:
                            nouns3 = sentence.index.find(second=prep.args.third, pos=POS.NN)
                            nouns3 = filter(lambda p: p != noun1, nouns3)
                            nouns3 = filter(lambda p: p != noun2, nouns3)
                            for noun3 in nouns3:
                                together2 = self.together(noun1.lemma, noun3.lemma)
                                together3 = self.together(noun2.lemma, noun3.lemma)
                                if together2 not in nn_pairs2 and together3 not in nn_pairs3:
                                    matches.append(Triple(self.rel_name, noun1, noun2, prep, noun3))
                                    nn_pairs1.append(together1)
                                    nn_pairs2.append(together2)
                                    nn_pairs3.append(together3)
        return matches


class DepNoun_NounEqualNoun(AbsDependencyRelation):
    """
    Example:
    noun_equal_noun(noun,noun) ("John is a biker") -> only if there is no prep attached to the second noun.
    """
    rel_name = "noun_equal_noun"

    def find_matches(self, sentence):
        matches = []
        for equal in sentence.index.find(extra="equal"):
            noun1 = sentence.index.find(second=equal.args.second, pos=POS.NN, return_set=True)
            if noun1:
                noun2 = sentence.index.find(second=equal.args.third, pos=POS.NN, return_set=True)
                if noun2 and noun1 != noun2:
                        preps = sentence.index.find(second=noun2.predicates[0].args.second, pos=POS.PREP)
                        if len(preps) == 0:
                            matches.append(Triple(self.rel_name, noun1, noun2))
        return matches


class DepNoun_NounPrepNoun(AbsDependencyRelation):
    """
    Example:
    noun_prep_noun(noun,prep,noun) ("house in London")
    """
    rel_name = "noun_prep_noun"

    def find_matches(self, sentence):
        matches = []
        nn_pairs = []
        for prep in sentence.index.find(pos=POS.PREP):
            nouns1 = sentence.index.find(second=prep.args.second, pos=POS.NN)
            for noun1 in nouns1:
                nouns2 = sentence.index.find(second=prep.args.third, pos=POS.NN)
                nouns2 = filter(lambda p: p != noun1, nouns2)
                for noun2 in nouns2:
                    together = self.together(noun1.lemma, noun2.lemma)
                    if together not in nn_pairs:
                        matches.append(Triple(self.rel_name, noun1, prep, noun2))
                        nn_paiappend(together)
        return matches


class DepNoun_NounPrepPrepNoun(AbsDependencyRelation):
    # TODO(zaytsev@usc.edu): implement this
    """
    Example:
    noun_prep_prep_noun(noun,prep,prep,noun) ("book out of the store")
    """
    rel_name = "noun_prep_prep_noun"


##################################
#                                #
#       OTHER RELATIONS          #
#                                #
##################################

class DepAny_Compl(AbsDependencyRelation):
    """
    Example:
    compl(anything,anything) ("близкий мне")
    """
    rel_name = "compl"

    def find_matches(self, sentence):
        matches = []
        for compl in sentence.index.find(extra="compl"):
            any_1s = \
                sentence.index.find(first=compl.args.second, pos=POS.VB) + \
                sentence.index.find(first=compl.args.second, pos=POS.RB) + \
                [sentence.index.find(first=compl.args.second, pos=POS.NN, return_set=True)] + \
                [sentence.index.find(first=compl.args.second, pos=POS.ADJ, return_set=True)] + \
                [sentence.index.find(second=compl.args.second, pos=POS.NN, return_set=True)] + \
                [sentence.index.find(second=compl.args.second, pos=POS.ADJ, return_set=True)]
            for any_1 in any_1s:
                any_2s = \
                    sentence.index.find(first=compl.args.third, pos=POS.VB) + \
                    sentence.index.find(first=compl.args.third, pos=POS.RB) + \
                    [sentence.index.find(first=compl.args.third, pos=POS.NN, return_set=True)] + \
                    [sentence.index.find(first=compl.args.third, pos=POS.ADJ, return_set=True)] + \
                    [sentence.index.find(second=compl.args.third, pos=POS.NN, return_set=True)] + \
                    [sentence.index.find(second=compl.args.third, pos=POS.ADJ, return_set=True)]
                for any_2 in any_2s:
                    if any_1 and any_2:
                        matches.append(Triple(self.rel_name, any_1, any_2))
        return matches


##################################
#                                #
#            MISC                #
#                                #
##################################


class TripleFold(object):

    def __init__(self):
        self.counter = collections.Counter()

    def add_triples(self, triples):
        for triple in triples:
            self.counter[triple.pack()] += 1

    def i_triples(self):
        for p_triple, freq in self.counter.most_common():
            triple = Triple.unpack(p_triple)
            yield triple + [freq]


class TripleExtractor():

    def __init__(self, triple_patterns=()):
        if len(triple_patterns) == 0:
            raise Exception("Extractor should have least 1 triple pattern.")
        self.triple_patterns = triple_patterns

    def i_extract_triples(self, i_sentences):
        for sent in i_sentences:
            matches = []
            for pattern in self.triple_patterns:
                matches.extend(pattern.find_matches(sent))
            yield matches


#
#
#      SOME `CONSTS`
#
#


RELATIONS = (
    DepVerb_SubjVerbDirobj(),
    DepVerb_SubjVerbIndirobj(),
    DepVerb_SubjVerbInstr(),
    DepVerb_SubjVerb(),
    DepVerb_PrepCompl(),
    DepVerb_SubjVerbVerbPrepNoun(),
    DepVerb_SubjVerbVerb(),
    DepAdj_NounAdj(),
    DepAdv_VerbNounAdv(),
    DepNoun_NounEqualPrepNoun(),
    DepNoun_NounNoun(),
    DepNoun_NounNounNoun(),
    DepNoun_NounEqualNoun(),
    DepNoun_NounPrepNoun(),
    DepAny_Compl(),
)

RELATION_NAMES = [rel.rel_name for rel in RELATIONS]

REL_NAME_ID_MAP = dict()
REL_ID_NAME_MAP = dict()
for rel in RELATIONS:
    REL_NAME_ID_MAP[rel.rel_name] = len(REL_NAME_ID_MAP)
    REL_ID_NAME_MAP[REL_NAME_ID_MAP[rel.rel_name]] = rel.rel_name


REL_POS_MAP = {
    REL_NAME_ID_MAP[DepVerb_SubjVerbDirobj.rel_name]: (POS.NN, POS.VB, POS.NN, ),
    REL_NAME_ID_MAP[DepVerb_SubjVerbIndirobj.rel_name]: (POS.NN, POS.VB, POS.NN, ),
    REL_NAME_ID_MAP[DepVerb_SubjVerbInstr.rel_name]: (POS.NN, POS.VB, POS.NN, ),
    REL_NAME_ID_MAP[DepVerb_SubjVerb.rel_name]: (POS.NN, POS.VB, ),
    REL_NAME_ID_MAP[DepVerb_PrepCompl.rel_name]: (POS.NN, POS.VB, POS.PREP, POS.NN, ),
    REL_NAME_ID_MAP[DepVerb_SubjVerbVerbPrepNoun.rel_name]: (POS.NN, POS.VB, POS.VB, POS.PREP, POS.NN, ),
    REL_NAME_ID_MAP[DepVerb_SubjVerbVerb.rel_name]: (POS.NN, POS.VB, POS.VB, ),
    REL_NAME_ID_MAP[DepAdj_NounAdj.rel_name]: (POS.NN, POS.ADJ, ),
    REL_NAME_ID_MAP[DepAdv_VerbNounAdv.rel_name]: (POS.NN, POS.VB, POS.RB, ),
    REL_NAME_ID_MAP[DepNoun_NounEqualPrepNoun.rel_name]: (POS.NN, POS.NN, POS.PREP, POS.NN, ),
    REL_NAME_ID_MAP[DepNoun_NounNoun.rel_name]: (POS.NN, POS.NN, ),
    REL_NAME_ID_MAP[DepNoun_NounNounNoun.rel_name]: (POS.NN, POS.NN, POS.NN, ),
    REL_NAME_ID_MAP[DepNoun_NounEqualNoun.rel_name]: (POS.NN, POS.NN, ),
    REL_NAME_ID_MAP[DepNoun_NounPrepNoun.rel_name]: (POS.NN, POS.PREP, POS.NN, ),
    REL_NAME_ID_MAP[DepAny_Compl.rel_name]: (POS.ANY, POS.ANY, ),
    REL_NAME_ID_MAP[DepNoun_NounEqualNoun.rel_name]: (POS.NN, POS.NN),
}


if len(REL_POS_MAP) != len(REL_NAME_ID_MAP):
    logging.error("NOT ALL RELATIONS HAS POS MAP")