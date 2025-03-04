import re
from scripts.utils import *
from scripts.annotator import output_maker
from spacy.matcher import DependencyMatcher
from spacy.matcher import Matcher
from spacy.matcher import PhraseMatcher
from spellchecker import SpellChecker

spell = SpellChecker()

def models(text, test_mode=False):
    def pp_time(sent):

        errors_pp = []
        all_errors = []
        dep_matcher = DependencyMatcher(vocab=nlp.vocab)
        present_perfect = [{'RIGHT_ID': 'verb', 'RIGHT_ATTRS': {'TAG': 'VBN', 'LEMMA': {'NOT_IN': ['get']}}},
                           {'LEFT_ID': 'verb', 'REL_OP': '>', 'RIGHT_ID': 'have',
                            'RIGHT_ATTRS': {'LEMMA': 'have', 'DEP': 'aux', 'TAG': {'IN': ['VBP', 'VBZ']}}}]
        dep_matcher.add("present_perfect", patterns=[present_perfect])
        results = dep_matcher(sent)
        if results:

            error_message = 'Present Perfect does not go along with indication of time in the past.'
            all_matches = []
            verbs = []
            dep_matcher_ = DependencyMatcher(vocab=nlp.vocab)

            # in/from/over/between + CD
            patt_one = [{'RIGHT_ID': 'prep', 'RIGHT_ATTRS':
                {'LEMMA': {'IN': ['from', 'in', 'over', 'between']}}},
                        {'LEFT_ID': 'prep', 'REL_OP': '>', 'RIGHT_ID': 'year',
                         'RIGHT_ATTRS': {'TAG': 'CD', 'DEP': 'pobj', 'lemma': {'NOT_IN': ['one']}}}]

            dep_matcher_.add('prep+cd', patterns=[patt_one])
            dep_matches = dep_matcher_(sent)

            # not recent/last
            if dep_matches and without_child(sent[dep_matches[0][1][1]].head, {'lemma_': ['last', 'recent']}):
                all_matches.append(dep_matches[0][1][0])
                if sent[dep_matches[0][1][0]].head.tag_ == 'VBN':
                    verbs.append(sent[dep_matches[0][1][0]].head)

            # in/from/over/between+year
            patt_two = [{'RIGHT_ID': 'prep', 'RIGHT_ATTRS': {'LEMMA': {'IN': ['at', 'over', 'in']}}},
                        {'LEFT_ID': 'prep', 'REL_OP': '>', 'RIGHT_ID': 'year',
                         'RIGHT_ATTRS': {'TAG': 'NN', 'LEMMA': 'year', 'DEP': 'pobj'}}]

            dep_matcher_.add('prep+year', patterns=[patt_two])

            # at/in/over + last/recent + NN
            patt_three = [{'RIGHT_ID': 'prep', 'RIGHT_ATTRS': {'LEMMA': {'IN': ['at', 'over', 'in']}}},
                          {'LEFT_ID': 'prep', 'REL_OP': '>', 'RIGHT_ID': 'noun',
                           'RIGHT_ATTRS': {'TAG': 'NN', 'DEP': {'IN': ['pobj', 'npadvmod']}}},
                          {'LEFT_ID': 'noun', 'REL_OP': '>', 'RIGHT_ID': 'adj',
                           'RIGHT_ATTRS': {'ORTH': {'IN': ['last', 'initial']}}}]

            dep_matcher_.add('prep+noun+last/initial', patterns=[patt_three])

            # at/in/over + ordinal + NN
            patt_four = [{'RIGHT_ID': 'prep', 'RIGHT_ATTRS': {'LEMMA': {'IN': ['at', 'over', 'in']}}},
                         {'LEFT_ID': 'prep', 'REL_OP': '>', 'RIGHT_ID': 'noun',
                          'RIGHT_ATTRS': {'TAG': 'NN', 'DEP': {'IN': ['pobj', 'npadvmod']}, 'LEMMA':
                              {'IN': ['year', 'term', 'week', 'semester', 'century'
                                                                          'day', 'month', 'decade', 'spring', 'fall',
                                      'autumn', 'winter', 'summer', 'night', 'evening',
                                      'morning', 'season', 'stage', 'point', 'phase']}}},
                         {'LEFT_ID': 'noun', 'REL_OP': '>', 'RIGHT_ID': 'ord_adj',
                          'RIGHT_ATTRS': {'ENT_TYPE': 'ORDINAL'}}]

            dep_matcher_.add('prep+noun+ordinal', patterns=[patt_four])

            # ago (but not since ...a long ago )
            find_ago = [ago for ago in sent if ago.lemma_ == 'ago']
            for ago_ in find_ago:
                if ago_.head.tag_ == 'VBN':
                    verbs.append(ago_.head)

            # last + noun of periods
            patt_five = [{'RIGHT_ID': 'noun', 'RIGHT_ATTRS': {'TAG': 'NN', 'DEP': {'IN': ['pobj', 'npadvmod']}, 'LEMMA':
                {'IN': ['year', 'term', 'week', 'semester', 'century'
                                                            'day', 'month', 'decade', 'spring', 'fall',
                        'autumn', 'winter', 'summer', 'night', 'evening',
                        'morning', 'season', 'stage', 'point', 'phase']}}},
                         {'LEFT_ID': 'noun', 'REL_OP': '>', 'RIGHT_ID': 'last', 'RIGHT_ATTRS': {'LEMMA': 'last'}}]

            dep_matcher_.add('last+nn', patterns=[patt_five])

            # since/from cd to cd
            patt_six = [{'RIGHT_ID': 'vbn', 'RIGHT_ATTRS': {'TAG': 'VBN'}},
                        {'LEFT_ID': 'vbn', 'REL_OP': '>', 'RIGHT_ID': 'prep',
                         'RIGHT_ATTRS': {'LEMMA': {'IN': ['from', 'since']}, 'DEP': 'prep'}},
                        {'LEFT_ID': 'prep', 'REL_OP': '>', 'RIGHT_ID': 'cd',
                         'RIGHT_ATTRS': {'TAG': 'CD', 'DEP': {'IN': ['pobj', 'npadvmod']}}},
                        {'LEFT_ID': 'vbn', 'REL_OP': '>', 'RIGHT_ID': 'to',
                         'RIGHT_ATTRS': {'LEMMA': 'to', 'DEP': 'prep'}},
                        {'LEFT_ID': 'to', 'REL_OP': '>', 'RIGHT_ID': 'cd_two', 'RIGHT_ATTRS': {'TAG': 'CD'}}]

            dep_matcher_.add('since_1998_to_2000', patterns=[patt_six])
            yesterday = [yestdy for yestdy in sent if yestdy.lemma_ == 'yesterday']
            for yestdy in yesterday:
                if yestdy.head.head.head.tag_ == 'VBN':
                    verbs.append(yestdy.head.head.head)
            # verb phrase extraction
            if dep_matcher_(sent):
                for match_dep in dep_matcher_(sent):
                    if nlp.vocab[match_dep[0]].text == 'prep+noun+last/initial' and not \
                            without_child(sent[match_dep[1][-1]].head, {'lemma_': 'the'}):
                        continue
                    if sent[match_dep[1][0]].head.tag_ == 'VBN':
                        verbs.append(sent[match_dep[1][0]].head)
                        if sent[match_dep[1][1]].lemma_ == 'since':
                            tok = sent[match_dep[1][1]]
                            all_errors.append([find_span([tok]),
                                               'You may need \'from\' instead of \'since\'.'])
            for verb in verbs:
                if not without_child(verb, {'lemma_': 'during'}):
                    continue
                if verb.tag_ == 'VBN':

                    have_not = [have for have in verb.children if have.lemma_ == 'have' and have.dep_ == 'aux'
                                and have.tag_ in {'VBZ', 'VBP'}]
                    if have_not:
                        have_not = have_not[0]
                        errors_pp.append(have_not)
                        not_ = [i for i in have_not.children if i.dep_ == 'neg' and i.norm_ == 'not']
                        if not_:
                            errors_pp.append(not_)
                        all_errors.append([find_span(errors_pp), error_message])
        return all_errors

    def inversion(sent):
        error_message = 'You may need inverted word order here.'

        def find_wrong_order(token_i):

            possible_inversions = {'barely', 'never', 'rarely', 'seldom',
                                   'scarcely', 'nowhere', 'neither', 'nor'}
            if token.i >= len(token.sent) - 1:
                return False
            if token_i.lemma_ in possible_inversions and not re.search(r'^Never the', token_i.sent.text):
                return True
            elif token_i.lemma_ in {'hardly'} and token.sent[token.i + 1].pos_ not in ['NOUN', 'PRON']:
                return True
            elif token_i.lemma_ == 'little' and token_i.dep_ in {'npadvmod', 'dobj', 'advmod'}:
                if without_child(token_i, {'lemma_': 'by'}):
                    return True
            elif token_i.lemma_ == 'not' and token_i.dep_ == 'preconj' and token.sent[token.i + 1].pos_ not in ['NOUN',
                                                                                                                'PRON']:
                flag_ = [i for i in token_i.children if i.lemma_ in {'only', 'since'}]
                if flag_:
                    return True

            return False

        for token in sent:
            flag = False
            if not (token.i - sent.start):
                prep_no_noun = [{'RIGHT_ID': 'prep',
                                 'RIGHT_ATTRS': {'LEMMA': {'IN': ['under', 'in', 'over', 'at', 'for', 'to']},
                                                 'TAG': 'IN'}},
                                {'LEFT_ID': 'prep', 'REL_OP': '>', 'RIGHT_ID': 'noun',
                                 'RIGHT_ATTRS': {'POS': 'NOUN'}},
                                {'LEFT_ID': 'noun', 'REL_OP': '>', 'RIGHT_ID': 'no', 'RIGHT_ATTRS': {'LEMMA': 'no'}}]
                no_sooner = [{'RIGHT_ID': 'no', 'RIGHT_ATTRS': {'LEMMA': 'no', 'DEP': 'neg'}},
                             {'LEFT_ID': 'no', 'REL_OP': '<', 'RIGHT_ID': 'noun',
                              'RIGHT_ATTRS': {'LEMMA': {'IN': ['soon', 'later']}}}]
                dep_matcher_ = DependencyMatcher(vocab=nlp.vocab)
                dep_matcher_.add('inversions', patterns=[prep_no_noun, no_sooner])
                for match_dep in dep_matcher_(sent):

                    if sent[match_dep[1][0]].i == token.i:
                        flag = True
                        del dep_matcher_
                        break
                if not flag:
                    flag = find_wrong_order(token)

                if flag:

                    verb = token.head if token.head.pos_ == 'AUX' or token.head.pos_ == 'VERB' else ''
                    if not verb:
                        aux = [v for v in token.head.children if v.pos_ == 'AUX']
                        verb_ = token.head if token.head.pos_ == 'VERB' else ''
                        aux_s = [v for v in token.head.head.children if v.pos_ == 'AUX']
                        verb2_ = token.head.head if token.head.head.pos_ == 'VERB' else ''
                        if aux:
                            verb = aux[0]
                        elif aux_s:
                            verb = aux_s[0]
                        elif verb_:
                            verb = verb_
                        elif verb2_:
                            verb = verb2_

                    if not isinstance(verb, str) and verb.pos_ == 'VERB':
                        aux_s = [v for v in token.head.head.children if v.pos_ == 'AUX']
                        if aux_s:
                            verb = aux_s[0]
                    if verb:

                        noun = [noun for noun in token.head.children if noun.dep_ in {'nsubj', 'nsubjpass'}]
                        noun = noun or [noun for noun in token.head.head.children if
                                        noun.dep_ in {'nsubj', 'nsubjpass'}]

                        if noun:
                            wrong_order = True if verb.i > noun[0].i else False
                            if wrong_order:
                                errors = []
                                errors.append([find_span([verb]), error_message])
                                return errors
            break
        return

    def inversion(sent):
        error_message = 'You may need inverted word order here.'

        def find_wrong_order(token_i):

            possible_inversions = {'barely', 'never', 'rarely', 'seldom',
                                   'scarcely', 'nowhere', 'neither', 'nor'}
            if token_i.lemma_ in possible_inversions and not re.search(r'^Never the', token_i.sent.text):
                return True
            elif token_i.lemma_ in {'hardly'} and token.sent[token.i + 1].pos_ not in ['NOUN', 'PRON']:
                if token_i.head.pos_ != 'VERB':
                    return True
            elif token_i.lemma_ == 'little' and token_i.dep_ in {'npadvmod', 'dobj', 'advmod'}:
                if without_child(token_i, {'lemma_': 'by'}):
                    return True
            elif token_i.lemma_ == 'not' and token_i.dep_ == 'preconj':
                if token_i.head.pos_ in ['NOUN', 'PRON']:
                    return False
                flag = [i for i in token_i.children if i.lemma_ in {'only', 'since'}]
                if flag:
                    return True
            elif token_i.lemma_ == 'only':
                # only + then/since/later/once
                flag = True if token_i.head.orth_ in {'then', 'since', 'later', 'once', 'in', 'by', 'with'} else False
                if flag:
                    return True
            return False

        for token in sent[:2]:
            flag = False
            if not (token.i - sent.start):
                prep_no_noun = [{'RIGHT_ID': 'prep',
                                 'RIGHT_ATTRS': {'LEMMA': {'IN': ['under', 'in', 'over', 'at', 'for', 'to']},
                                                 'TAG': 'IN'}},
                                {'LEFT_ID': 'prep', 'REL_OP': '>', 'RIGHT_ID': 'noun',
                                 'RIGHT_ATTRS': {'POS': 'NOUN'}},
                                {'LEFT_ID': 'noun', 'REL_OP': '>', 'RIGHT_ID': 'no', 'RIGHT_ATTRS': {'LEMMA': 'no'}}]
                no_sooner = [{'RIGHT_ID': 'no', 'RIGHT_ATTRS': {'LEMMA': 'no', 'DEP': 'neg'}},
                             {'LEFT_ID': 'no', 'REL_OP': '<', 'RIGHT_ID': 'noun',
                              'RIGHT_ATTRS': {'LEMMA': {'IN': ['soon', 'later']}}}]
                dep_matcher_ = DependencyMatcher(vocab=nlp.vocab)
                dep_matcher_.add('inversions', patterns=[prep_no_noun, no_sooner])
                for match_dep in dep_matcher_(sent):
                    if sent[match_dep[1][0]].i == token.i:
                        flag = True
                        del dep_matcher_
                        break
                if not flag:
                    try:
                        flag = find_wrong_order(token)
                    except:
                        continue
                if flag:
                    verb = token.head if token.head.pos_ == 'AUX' or token.head.pos_ == 'VERB' else ''
                    if not verb:
                        aux = [v for v in token.head.children if v.pos_ == 'AUX']
                        verb_ = token.head if token.head.pos_ == 'VERB' else ''
                        aux_s = [v for v in token.head.head.children if v.pos_ == 'AUX']
                        verb2_ = token.head.head if token.head.head.pos_ == 'VERB' else ''
                        if aux:
                            verb = aux[0]
                        elif aux_s:
                            verb = aux_s[0]
                        elif verb_:
                            verb = verb_
                        elif verb2_:
                            verb = verb2_
                    if not isinstance(verb, str) and verb.pos_ == 'VERB':
                        aux_s = [v for v in token.head.head.children if v.pos_ == 'AUX']
                        if aux_s:
                            verb = aux_s[0]
                    if verb:
                        noun = [noun for noun in token.head.children if noun.dep_ in {'nsubj', 'nsubjpass'}]
                        noun = noun or [noun for noun in token.head.head.children if
                                        noun.dep_ in {'nsubj', 'nsubjpass'}]
                        if noun:
                            wrong_order = True if verb.i > noun[0].i else False
                            if wrong_order:
                                errors = []
                                errors.append([find_span([verb]), error_message])
                                return errors
            break
        return

    def only(sent):
        error_message = 'You may need inverted word order here.'
        # inverted order is needed in the second clause
        only_ = [{'RIGHT_ID': 'only', 'RIGHT_ATTRS': {'LEMMA': 'only', 'DEP': 'advmod'}},
                 {'LEFT_ID': 'only', 'REL_OP': '<', 'RIGHT_ID': 'advcl', 'RIGHT_ATTRS':
                     {'POS': {'IN': ['AUX', 'VERB']}, 'DEP': 'advcl'}},
                 {'LEFT_ID': 'advcl', 'REL_OP': '>', 'RIGHT_ID': 'when_if', 'RIGHT_ATTRS':
                     {'LEMMA': {'IN': ['when', 'if', 'after']}}},
                 {'LEFT_ID': 'advcl', 'REL_OP': '<', 'RIGHT_ID': 'verb', 'RIGHT_ATTRS': {'DEP': 'ROOT'}}]
        not_until = [{'RIGHT_ID': 'not', 'RIGHT_ATTRS': {'LEMMA': 'not', 'DEP': 'neg'}},
                     {'LEFT_ID': 'not', 'REL_OP': '<', 'RIGHT_ID': 'advcl', 'RIGHT_ATTRS':
                         {'POS': {'IN': ['AUX', 'VERB']}, 'DEP': 'advcl'}},
                     {'LEFT_ID': 'advcl', 'REL_OP': '>', 'RIGHT_ID': 'until', 'RIGHT_ATTRS': {'LEMMA': 'until'}},
                     {'LEFT_ID': 'advcl', 'REL_OP': '<', 'RIGHT_ID': 'verb',
                      'RIGHT_ATTRS': {'DEP': 'ROOT'}}]
        dep_matcher_ = DependencyMatcher(vocab=nlp.vocab)
        dep_matcher_.add('only_not_until', patterns=[only_, not_until])
        if dep_matcher_(sent):
            if sent[dep_matcher_(sent)[0][1][0]].head.pos_ in ['NOUN', 'PRON']:
                return []
            verb = sent[dep_matcher_(sent)[0][1][-1]]
            aux_s = [i for i in verb.children if i.dep_ == 'aux']
            noun = [n for n in verb.children if n.dep_ in ['nsubj', 'nsubjpass']]
            if noun:
                noun = noun[0]
                if aux_s:
                    verb = aux_s[0]
                if noun.i < verb.i:
                    del dep_matcher_;
                    return [[find_span([verb]), error_message]]
        return

    def extra_inversion(sent):
        error_message = 'You may have used the wrong word order.'
        if '"' not in sent.text and '"' not in sent.text:
            dep_matcher_ = DependencyMatcher(vocab=nlp.vocab)
            ccomp_ = [{'RIGHT_ID': 'verb', 'RIGHT_ATTRS': {'DEP': 'ROOT'}},
                      {'LEFT_ID': 'verb', 'REL_OP': '>', 'RIGHT_ID': 'ccomp', 'RIGHT_ATTRS': {'DEP': 'ccomp'}}]
            dep_matcher_.add('ccomp_', patterns=[ccomp_])
            if dep_matcher_(sent):
                ccomp = sent[dep_matcher_(sent)[0][1][-1]]
                i = ccomp.i
                del dep_matcher_
                dep_matcher_ = DependencyMatcher(vocab=nlp.vocab, validate=True)

                wrb = [{'RIGHT_ID': 'ccomp', 'RIGHT_ATTRS': {'DEP': 'ccomp'}},
                       {'LEFT_ID': 'ccomp', 'REL_OP': '>', 'RIGHT_ID': 'wrb',
                        'RIGHT_ATTRS': {'DEP': 'advmod', 'TAG': 'WRB'}}]

                whether_if = [{'RIGHT_ID': 'ccomp', 'RIGHT_ATTRS': {'DEP': 'ccomp'}},
                              {'LEFT_ID': 'ccomp', 'REL_OP': '>', 'RIGHT_ID': 'sconj',
                               'RIGHT_ATTRS': {'DEP': 'mark', 'POS': 'SCONJ', 'LEMMA': {'IN': ['whether', 'if']}}}]
                dep_matcher_.add('wrb', patterns=[wrb, whether_if])
                for match in dep_matcher_(sent):
                    ccomp_verb = sent[match[1][0]]
                    noun = [i for i in ccomp_verb.children if i.dep_ in ['nsubj', 'nsubjpass']]
                    aux = [i for i in ccomp_verb.children if i.pos_ == 'AUX']
                    if noun and aux:
                        if aux[0].i < noun[0].i:
                            words = [sent[k] for k in range(aux[0].i - sent.start, noun[0].i + 1 - sent.start)]
                            return [[find_span(words), error_message]]
            return

    def spelling(sent):

        errors = []
        for token in sent:
            if len(token.text) < 4 or token.text[0].isupper(): continue;
            if str(spell.correction(token.text)) != str(token.text):
                candidates_l = list(spell.candidates(token.text))[:2]
                candidates = "/".join(candidates_l)
                errors.append([find_span([token]),
                               f'You might have misspelled that word, possible '
                               f'corrections: {candidates}.'])
        return errors

    def hardly(sent):
        hardly = [
            {'RIGHT_ID': 'hardly', 'RIGHT_ATTRS': {'DEP': 'advmod', 'LEMMA': {'IN': ['hardly', 'scarcely', 'barely']}}},
            {'LEFT_ID': 'hardly', 'REL_OP': '<', 'RIGHT_ID': 'verb', 'RIGHT_ATTRS': {'POS': 'VERB'}}]

        no_sooner = [{'RIGHT_ID': 'sooner', 'RIGHT_ATTRS': {'DEP': 'advmod', 'LEMMA': 'soon'}},
                     {'LEFT_ID': 'sooner', 'REL_OP': '<', 'RIGHT_ID': 'verb', 'RIGHT_ATTRS': {'POS': 'VERB'}},
                     {'LEFT_ID': 'sooner', 'REL_OP': '>', 'RIGHT_ID': 'no',
                      'RIGHT_ATTRS': {'DEP': 'neg', 'LEMMA': 'no'}}]
        dep_matcher_ = DependencyMatcher(vocab=nlp.vocab)
        dep_matcher_.add('hardly', patterns=[hardly])
        dep_matcher_.add('sooner', patterns=[no_sooner])
        errors = []
        if dep_matcher_(sent):
            if not sent[dep_matcher_(sent)[0][1][0]].i - sent.start:
                matched = nlp.vocab[dep_matcher_(sent)[0][0]]
                root_ = sent.root
                advcls = [x for x in sent if x.dep_ == 'advcl']
                if advcls:
                    advcl = advcls[0]
                    conj = ''
                    allowed = ''
                    if matched.text == 'hardly':
                        conj = [wh for wh in advcl.children if wh.dep_ == 'advmod' and wh.lemma_ in {'when', 'before'}]
                        allowed = '\'when\' or \'before\''
                    else:
                        conj = [wh for wh in advcl.children if wh.dep_ == 'mark' and wh.lemma_ == 'than']
                        allowed = 'than'
                    if not conj:
                        hardly = sent[dep_matcher_(sent)[0][1][0]]
                        errors.append([find_span([hardly]),
                                       f'With such a construction of the main clause, the next clause should be introduced with {allowed}.'])

                    if not (sent[dep_matcher_(sent)[0][1][0]].tag_ == 'VBN' and [aux for aux in
                                                                                 sent[dep_matcher_(sent)[0][1][
                                                                                     0]].children
                                                                                 if
                                                                                 aux.dep_ == 'aux' and aux.pos_ == 'VBD' and aux.lemma_ == 'have']):
                        errors.append([find_span([sent[dep_matcher_(sent)[0][1][0]]]),
                                       'Past Perfect should be used in the main clause.'])
                    for clause in advcls:
                        verb = clause

                        if not (verb.tag_ == 'VBD' and without_child(verb, {'pos_': 'AUX', 'dep_': 'aux'})):
                            errors.append([find_span([verb]), 'Past Simple should be used in this clause.'])
            return errors

    def conditionals(sent):
        if [x for x in sent if x.lemma_ in {'if'}]:
            root = sent.root if sent.root.pos_ == 'VERB' else ''
            if root:
                errors = []
                will = [x for x in root.children if x.dep_ == 'aux' and x.lemma_ == 'will']
                would = [x for x in root.children if
                         x.dep_ == 'aux' and x.lemma_ == 'would' and x.head.lemma_ != 'like']
                advcls = [x for x in sent if x.dep_ == 'advcl' and [y for y in x.children if
                                                                    y.lemma_ in {'if'} and y.dep_ == 'mark']]
                for advcl in advcls:
                    ss = 'http://realec-reference.site/viewArticle/CONDITIONAL%20SENTENCES'
                    will_if_clause = [x for x in advcl.children if x.dep_ == 'aux' and x.lemma_ in {'will', 'would'}]
                    if will_if_clause:
                        errors.append([find_span([will_if_clause[0]]),
                                       '\'Will\' or \'would\' after \'if\' are not used in conditionals.'])
                    verb = advcl
                    if will:
                        have = [have for have in verb.children if
                                (have.lemma_ == 'have' and have.dep_ == 'aux' and have.tag_ in {'VBP', 'VBZ'})]
                        pres_perfect = True if verb.tag_ == 'VBN' and have else False
                        pres_simple = True if verb.tag_ in {'VB', 'VBP', 'VBZ'} else False
                        if not (pres_perfect | pres_simple):
                            errors.append([find_span([verb]),
                                           'In if-clauses talking about future, Present Simple or Present Perfect are expected. (More examples: http://realec-reference.site/viewArticle/CONDITIONAL%20SENTENCES )'])
                    elif would:
                        past_perfect = True if verb.tag_ == 'VBN' \
                                               and [have for have in verb.children if have.dep_ == 'aux' \
                                                    and have.text == 'had'] else False
                        past_simple = True if verb.tag_ == 'VBD' \
                                              and without_child(verb, {'dep_': 'aux'}) else False
                        if not (past_perfect | past_simple):
                            errors.append([find_span([verb]),
                                           r'In if-clauses talking about unreal conditions, Past Simple or '
                                           r'Past Perfect are expected.(More examples: '
                                           r'http://realec-reference.site/viewArticle/CONDITIONAL%20SENTENCES) '])
                return errors

    def that_comma(sent):
        error_that = DependencyMatcher(vocab=nlp.vocab)
        comma_that = [{'RIGHT_ID': 'comma', 'RIGHT_ATTRS': {"LEMMA": ",", "POS": "PUNCT"}},
                      {'LEFT_ID': 'comma', 'REL_OP': '.', 'RIGHT_ID': 'that', 'RIGHT_ATTRS': {'LEMMA': 'that'}}]
        error_that.add('comma_that', [comma_that])
        if error_that(sent):
            found_subj = [token.i for token in sent if 'subj' in str(token.dep_)]
            found_subj.sort()
            errors = []
            for match in error_that(sent):
                that = sent[match[1][-1]]
                if 'subj' in str(that.dep_):
                    if that.i != found_subj:  # no cases as Unfortunately, that
                        errors.append([find_span([sent[match[1][0]], that]),
                                       'Instead of the comma, semicolon has to be used in front of \'that\'.'])
            first_that = sent[error_that(sent)[0][1][-1]]
            if first_that.dep_ == 'mark':
                errors.append([find_span([sent[error_that(sent)[0][1][0]], first_that]),
                               'You may have used a redundant comma in front of \'that\'.'])
            return errors
        return

    def punct(sent):
        comment = """A comma seems to be missing."""
        errs = []
        re_find_b = [r"(From [a-z].? (?:point of view|viewpoint|perspective))",
                     r"(From [A-Z][a-z]+'s (?:point of view|viewpoint|perspective))",
                     r'(To [a-z]{2,5} mind)', r'For (?:example|instance)', r'(However|Nevertheless|Consequently|To start with|Firstly| \
        Secondly|Thirdly|Moreover|On the other hand|In other words|In short|Surprisingly| \
        Unsurprisingly|Hopefully|Interestingly|Obviously|In conclusion|To conclude|To sum up| \
        Thus|Of course)']

        re_check_b = [r'From [a-z]{2,5} (?:point of view|viewpoint|perspective), ',
                      r"From [A-Z][a-z]+'s (?:point of view|viewpoint|perspective), ",
                      r'To [a-z]{2,5} mind, ', r'For (?:example|instance), ', r'(?:However|Nevertheless|Consequently|To start with|Firstly| \
        Secondly|Thirdly|Moreover|On the other hand|In other words|In short|Surprisingly| \
        Unsurprisingly|Hopefully|Interestingly|Obviously|In conclusion|To conclude|To sum up| \
        Thus|Of course), ']

        re_find_m = [r"(from [a-z]{2,5} (?:point of view|viewpoint|perspective))",
                     r'(to [a-z]{2,5} mind)',
                     r'(for (?:example|instance))',
                     r'(however|nevertheless|consequently|to start with|firstly|secondly|thirdly|moreover|on the other hand|in other words|in short|surprisingly|\
        unsurprisingly|hopefully|interestingly|obviously|in conclusion|to conclude|to sum up|thus|of course)']
        re_check_m = [r'.*, from [a-z]{2,5} (?:point of view|viewpoint|perspective), ', r'.*, to [a-z]{2,5} mind, ',
                      r'.*, for (?:example|instance), ',
                      r'(?:however|nevertheless|consequently|to start with|firstly|secondly|thirdly|moreover|on the other hand|in other words|in short|surprisingly|unsurprisingly|hopefully|interestingly|obviously|in conclusion|to conclude|to sum up|thus|of course), ']
        re_trigger1 = [r'.* (?:вЂ”|-|:) from [a-z]{2,5} (?:point of view|viewpoint|perspective), ',
                       r'.* (?:вЂ”|-|:) to [a-z]{2,5} mind, ',
                       r'.* (?:вЂ”|-|:) for (?:example|instance), ', r'.* (?:вЂ”|-|:) (?:however|nevertheless|consequently|to start with|firstly| \
        secondly|thirdly|moreover|on the other hand|in other words|in short|surprisingly| \
        unsurprisingly|hopefully|interestingly|obviously|in conclusion|to conclude|to sum up| \
        thus|of course), ']
        re_trigger2 = [r'.*, from [a-z]{2,5} (?:point of view|viewpoint|perspective) (?:вЂ”|-|:|.)',
                       r'.*, to [a-z]{2,5} mind (?:вЂ”|-|:|.) (?:вЂ”|-|:|.)',
                       r'.*, for (?:example|instance) (?:вЂ”|-|:|.)', r'.*, (?:however|nevertheless|consequently|to start with|firstly| \
        secondly|thirdly|moreover|on the other hand|in other words|in short|surprisingly| \
        unsurprisingly|hopefully|interestingly|obviously|in conclusion|to conclude|to sum up| \
        thus|of course) (?:вЂ”|-|:|.)']

        for pattern in re_find_b:
            if re.search(pattern, sent.text):
                found = 0
                for true_pattern in re_check_b:
                    if re.search(true_pattern, sent.text):
                        found = 1
                        break
                if found == 0:
                    m = re.search(pattern, sent.text).span()
                    start, end = m
                    span = sent.char_span(start, end)
                    errs.append([[sent.start + start, sent.start + end], comment])

        for pattern in re_find_m:
            if re.search(pattern, sent.text):
                found = 0
                for true_pattern in re_check_m:
                    if re.search(true_pattern, sent.text):
                        found = 1
                        break
                for also_true_pattern in re_trigger1:
                    if re.search(also_true_pattern, sent.text):
                        found = 1
                        break
                for also_true_pattern in re_trigger2:
                    if re.search(also_true_pattern, sent.text):
                        found = 1
                        break
                if found == 0:
                    m = re.search(pattern, sent.text).span()
                    start, end = m
                    span = sent[start:end]
                    errs.append([[sent.start + start, sent.start + end], comment])

        return errs

    def redundant_comma(sent):
        error_clause = DependencyMatcher(vocab=nlp.vocab)
        wh_clause = [{'RIGHT_ID': 'root', 'RIGHT_ATTRS': {'DEP': {'IN': ['ROOT', 'ccomp']}}},
                     {'LEFT_ID': 'root', 'REL_OP': '>', 'RIGHT_ID': 'ccomp', 'RIGHT_ATTRS': {'DEP': 'ccomp'}},
                     {'LEFT_ID': 'ccomp', 'REL_OP': '>', 'RIGHT_ID': 'wrb',
                      'RIGHT_ATTRS': {'TAG': {'IN': ['WP', 'WRB']}}},
                     {'LEFT_ID': 'wrb', 'REL_OP': ';', 'RIGHT_ID': 'punct', 'RIGHT_ATTRS': {'POS': 'PUNCT'}}]
        whether_clause = [{'RIGHT_ID': 'root', 'RIGHT_ATTRS': {'DEP': {'IN': ['ROOT', 'ccomp']}}},
                          {'LEFT_ID': 'root', 'REL_OP': '>', 'RIGHT_ID': 'ccomp', 'RIGHT_ATTRS': {'DEP': 'ccomp'}},
                          {'LEFT_ID': 'ccomp', 'REL_OP': '>', 'RIGHT_ID': 'whether',
                           'RIGHT_ATTRS': {'DEP': 'mark', 'LEMMA': {'IN': ['whether', 'if']}}},
                          {'LEFT_ID': 'whether', 'REL_OP': ';', 'RIGHT_ID': 'punct', 'RIGHT_ATTRS': {'POS': 'PUNCT'}}]
        error_clause.add('wh_clause', [wh_clause, whether_clause])
        errors = []
        first = True
        for match in error_clause(sent):
            if first:
                if 'subj' not in sent[match[1][-2]].dep_:
                    first = False
                    errors.append([find_span([sent[match[1][-1]], sent[match[1][-2]]]),
                                   'You may have used a redundant comma in front of this conjunction.'])
        return errors

    def past_cont(sent):
        p_cont = [{'RIGHT_ID': 'vbg', 'RIGHT_ATTRS': {'TAG': 'VBG'}},
                  {'LEFT_ID': 'vbg', 'REL_OP': '>', 'RIGHT_ID': 'was',
                   'RIGHT_ATTRS': {'DEP': 'aux', 'TAG': 'VBD', 'ORTH': {'IN': ['was', 'were']}}}]
        error_clause = DependencyMatcher(vocab=nlp.vocab)
        error_clause.add('p_cont', [p_cont])
        for match in error_clause(sent):
            verb = sent[match[1][0]]
            errors = []
            if without_child(verb, {'dep_': 'advmod', 'tag_': 'RB'}):
                advcls = [x for x in verb.children if x.dep_ in {'relcl', 'advcl'}]
                advcls = advcls or [x for x in sent if x.dep_ in {'relcl', 'advcl'}]
                while_ = False
                for advcl in advcls:
                    if any([while_.dep_ == 'mark'
                            and while_.lemma_ in {'as', 'while'} for while_ \
                            in advcl.children]): while_ = True;break;
                if re.search(r'(always|never|forever|constantly|permanently|eternally|ever)', sent.text):
                    return errors
                if not while_ or errors:
                    errors.append([find_span([sent[match[1][1]], sent[match[1][0]]]),
                                   'The usage of Past Continuous might be erroneous.'])
            return errors
        return

    def consider_that(sent):
        error_message = 'You may have wrongly used the verb CONSIDER with THAT.'
        consider_that_errs = []
        consider_that = [{'LEMMA': 'consider'}, {'LEMMA': 'that'}]
        matcher = Matcher(vocab=nlp.vocab)
        matcher.add("consider_that", patterns=[consider_that])
        for matched in matcher(sent):
            consider_that_errs.append([find_span([sent[matched[1]], sent[matched[2]]]), error_message])
        return consider_that_errs

    def agreement_s_v(sent):
        errors_ = []
        ambiguous = {'bison', 'cod', 'deer', 'fish', 'moose', 'boar', 'salmon', 'sheep',
                     'shrimp', 'swine', 'trout', 'buffalo', 'grouse', 'elk', 'fruit', 'reindeer',
                     'offspring', 'pike',
                     'statistics', 'politics', 'mechanics', 'economics',
                     'government', 'data', 'police', 'team', 'jury', 'family',
                     'half', 'class', 'majority', 'part', 'percent', '%', 'cent', 'lot'}

        sing_only = {'each', 'either', 'neither', 'one', 'nobody',
                     'nothing', 'anyone', 'anybody', 'anything', 'someone',
                     'somebody', 'something', 'everyone', 'everybody', 'everything',
                     'this', 'one', 'other', 'measles'}

        plur_only = {'several', 'few', 'many', 'both', 'these', 'those'}

        def find_subj(pred):
            # simple cases
            subjects = []
            subjects = [child for child in list(pred.children) if child.dep_.startswith(('nsubj', 'csubj'))]

            # handling 'there is' and 'there are' cases
            if pred.lemma_ == 'be' and 'there' in list(i.text.lower() for i in pred.children):
                subjects += [child for child in list(pred.children) if child.dep_ == 'attr']

            # if predicate is an auxiliary, we want to take subjects of its head
            if pred.dep_.startswith('aux'):
                subjects += [child for child in list(pred.head.children) if child.dep_.startswith(('nsubj', 'csubj'))]

            # handling conjuncts: multiple subjects as in 'Mother and father are key figures in a child's life'.
            add_subj = []
            for subject in subjects:
                add_subj += list(subject.conjuncts)

            cur_pred = pred
            while len(subjects) == 0 and cur_pred.dep_ == "conj":
                cur_pred = cur_pred.head
                subjects = find_subj(cur_pred)

            subjects += add_subj

            # the subjects' order may be different from sentence order, so we arrange it right
            subjects.sort(key=lambda subj: subj.i)

            return subjects

        def find_pred_subj(doc):
            pred_sub = list()
            for token in doc:
                if token.pos_ in ['AUX', 'VERB']:
                    # negation: cases like "He doesn't scare me"
                    aux = None
                    if [ch for ch in list(token.lefts) if ch.dep_ == 'neg']:
                        children = list(token.children)
                        for ch in children:
                            if ch.dep_ == 'aux' and not aux:
                                aux = ch
                        if aux:
                            pred_sub += [(aux, find_subj(aux))]

                    # if the predicate is analytical like 'I have done',
                    # spacy rightfully considers the participle to be the root,
                    # but we need grammatical info, so we will consider aux the root
                    if not aux:  # for when negation is expressed with 'never' etc and does not need aux support
                        if token.tag_ in ['VBN', 'VBG']:
                            aux = None
                            children = list(token.children)
                            for ch in children:
                                if ch.dep_ == 'aux' and ch.pos_ in ['VERB', 'AUX'] and ch.tag_ != 'VBN':
                                    aux = ch
                                elif not aux and ch.dep_ == 'auxpass' and ch.pos_ in ['VERB', 'AUX']:
                                    aux = ch
                            if aux:
                                pred_sub += [(aux, find_subj(aux))]

                        # all other cases
                        elif token.dep_ in ['ROOT', 'ccomp', 'xcomp', 'acl', 'relcl']:
                            pred_sub += [(token, find_subj(token))]

                        # conjuncts: when there are multiple predicates connected by conjunction
                        elif token.dep_ == 'conj' and token.head.dep_ in ['ROOT', 'ccomp', 'xcomp', 'acl', 'relcl']:
                            pred_sub += [(token, find_subj(token))]

            return pred_sub

        def errors(ps):
            res = []
            for pair in ps:
                subj_agr, pred_agr = None, None  # what each must agree with, variables must coincide in the end
                pred = pair[0]
                subj = pair[1]
                if len(subj) == 1:
                    subject = subj[0]
                    s = subject.text.lower()
                    subject_left_children = subject.lefts
                    subject_is_numeral = False
                    for child in subject_left_children:
                        if child.pos_ == 'NUM':
                            subject_is_numeral = True
                            break
                    if subject_is_numeral:
                        continue
                    if s not in ambiguous:
                        children = list(ch for ch in subject.children)
                        children_text = list(ch.text.lower() for ch in children)

                        # singular only pronouns
                        if s in sing_only or subject.ent_type_ == 'ORG':
                            subj_agr = 'sg'
                        elif subject.tag_ == 'VB':
                            subj_agr = 'sg'

                        # either singular or plural pronouns
                        # if they have an 'of N, N, N...', after them we will require check if verb agrees with the last noun
                        elif (s in {'some', 'any', 'none', 'all', 'most'}
                              and 'of' in children_text):
                            of = [ch for ch in children if ch.text.lower() == 'of'][0]
                            noun = [ch for ch in of.children if ch.pos_ == 'NOUN']
                            if noun:
                                noun = noun[0]
                                while [ch for ch in noun.children if (ch.dep_ == 'conj' and ch.pos_ == 'NOUN')]:
                                    noun = [ch for ch in noun.children if (ch.dep_ == 'conj' and ch.pos_ == 'NOUN')][-1]
                                if noun.tag_ in ['NNS', 'NNPS'] or noun.text.lower() in plur_only:
                                    subj_agr = 'pl'
                                elif noun.tag_ in ['NN', 'NNP'] or noun.text.lower() in sing_only:
                                    subj_agr = 'sg'

                        # plural only pronouns
                        elif s in plur_only and not children:
                            subj_agr = 'pl'

                        elif s in {'i', 'we', 'you', 'they'}:
                            subj_agr = 'pl'
                        elif s in {'he', 'she', 'it'}:
                            subj_agr = 'sg'

                        elif s == 'number':
                            if 'a' in children_text and 'of' in children_text:
                                subj_agr = 'pl'
                            else:
                                subj_agr = 'sg'

                        # predicates in non-head clauses with 'who', 'that' agree with noun in head clause
                        elif s in ['who', 'that', 'which']:
                            if pred.dep_ == 'relcl':
                                # why relcl? we can only be sure about this tag that it is the case we're looking for.
                                # other possible predicate tags include '...comp', but these also apply
                                # in cases like "I asked the boys who was the winner",
                                # which, although with incorrect word order,
                                # are still clearly present in Russian essays
                                # and will be parsed by spacy as 'ccomp'
                                head = pred.head
                                if not head.conjuncts:
                                    if head.tag_ in ['NNS', 'NNPS'] or head.text.lower() in plur_only:
                                        subj_agr = 'pl'
                                    elif head.tag_ in ['NN', 'NNP'] or head.text.lower() in sing_only:
                                        subj_agr = 'sg'
                                else:
                                    conjuncts = list(head.conjuncts) + [head]
                                    for conjunct in conjuncts:
                                        if 'and' in list(child.text.lower() for child in conjunct.children):
                                            subj_agr = 'pl'
                        elif subject.tag_ in ['NNS', 'NNPS']:
                            subj_agr = 'pl'
                        elif subject.tag_ in ['NN', 'NNP', 'VBG']:
                            subj_agr = 'sg'
                        if subject.ent_type_ == 'LOC' or subject.ent_type_ == 'GPE':
                            if subject.tag_ in ['NNS', 'NNPS']:
                                continue
                            else:
                                subj_arg = 'sg'

                elif len(subj) > 1:
                    # 'Mother, father and brother were present.'
                    # If conjuncts are connected by 'and', he predicate is plural
                    # Exception: 'Every man, woman and child aprticipates in the tournament.'
                    if 'and' in list(
                            child.text.lower() for child in list(list(subj[0].children) + list(subj[-2].children))):
                        left_subj_children = list(child.text.lower() for child in list(subj[0].lefts))
                        left_pred_children = list(child.text.lower() for child in list(pred.lefts))
                        is_uppercase = True
                        all_gerund = True
                        for sub in subj:
                            if sub.tag_ != 'NNP':
                                is_uppercase = False
                                break
                            if sub.tag_ != 'VBG':
                                all_gerund = False
                        # Don't check: 'Playing football and enjoying it + is a good thing | are different things)'
                        if all_gerund:
                            continue
                        # Don't check: 'Jones and Sons is a respectable company.'
                        if is_uppercase:
                            continue
                        # Don't check: 'There is Tom and Mary as a perfect example.'
                        if pred.text.lower() in ['is', 'are'] and 'there' in left_pred_children:
                            continue
                        if 'every' in left_subj_children or 'each' in left_subj_children:
                            subj_agr = 'sg'
                        else:
                            subj_agr = 'pl'
                    # 'Mother, father or brother comes to pick up the kid.'
                    # If conjuncts are connected by 'or', verb agrees with the last one
                    elif any(a in list(
                            child.text.lower() for child in list(list(subj[0].children) + list(subj[-2].children))) for
                             a in ['or', 'nor']):
                        if subj[-1].tag_ in ['NNS', 'NNPS'] or subj[-1].text.lower() in plur_only:
                            subj_agr = 'pl'
                        elif subj[-1].tag_ in ['NN', 'NNP', 'VBG'] or subj[-1].text.lower() in sing_only:
                            subj_agr = 'sg'

                if pred.tag_ == 'VBZ':
                    pred_agr = 'sg'
                elif pred.tag_ == 'VBP':
                    pred_agr = 'pl'
                elif pred.lemma == 'be':
                    if pred.text == 'was':
                        pred_agr = 'sg'
                    elif pred.text == 'were':
                        pred_agr = 'pl'

                if subj_agr != pred_agr and subj_agr and pred_agr:
                    res += [pair]

            return res

        ps = find_pred_subj(sent)
        er = errors(ps)
        for e in er:
            er_span = []
            for part in e:
                if isinstance(part, list):
                    er_span.extend(part)
                else:
                    er_span.append(part)

            errors_.append([find_span(er_span),
                            'It seems that the subject and predicate are not in agreement.'])
        return errors_

    def gerund(sent):

        errs = []
        if not re.search('of', sent.text): return errs
        with open('scripts/gerund_errors.txt', 'r') as fw:
            words = fw.read()
        gerund = words.split('\n')
        for word in gerund:
            if not re.search(word, sent.text, flags=re.I): continue
            matcher = PhraseMatcher(nlp.vocab, attr='LOWER')
            matcher.add("gerund", [nlp(word)])
            matches = matcher(sent)
            if matches:
                for m in matches:
                    child_ = [of for of in sent[m[-2] - sent.start].children if of.dep_ == 'prep' and of.lemma_ == 'of']
                    if child_:
                        child_.append(sent[m[-2] - sent.start])
                        errs.append([find_span(child_),
                                     'This gerund needs direct object.'])
                        return errs
        return errs

    def prep(sent):
        errs = []
        with open("scripts/noun_prep.txt", 'r', encoding='utf-8') as file:
            raw = file.read()
            nounpreps = raw.split('\n')
        nouns = []
        for phrase in nounpreps:
            words = phrase.split(" ")
            noun = words[0]
            if noun not in nouns:
                nouns.append(noun)
        for noun in nouns:
            if not re.search(noun, sent.text, flags=re.I): continue
            matcher = PhraseMatcher(nlp.vocab, attr='LOWER')
            matcher.add("noun", [nlp(noun)])
            matches = matcher(sent)
            for m in matches:
                if sent[m[-2] - sent.start].pos_ != 'NOUN': continue
                child_ = [of for of in sent[m[-2] - sent.start].children if
                          of.dep_ == 'prep' and of.i > sent[m[-2] - sent.start].i and of.text != 'to']
                child_ = [prep_ for prep_ in child_ if noun + ' ' + prep_.text in nounpreps]
                if not child_:
                    child_ = [prep_ for prep_ in child_ if noun + ' ' + prep_.text not in nounpreps]
                    if not len(child_): continue
                    child_.append(sent[m[-2] - sent.start])

                    errs.append([find_span(child_),
                                 "This noun is frequently used with a different preposition. \
                                 Check out possible combinations at \
                                 http://realec-reference.site/articlesByTag/Prepositions"])
                    return errs
        return errs

    def adj(sent):
        errs = []
        with open('scripts/adj.txt', 'r', encoding='utf-8') as file:
            raw = file.read()
            adj_phrase = raw.split('\n')
        adjs = []
        for phrase in adj_phrase:
            words = phrase.split(' ')
            adj = words[0]
            if adj not in adjs:
                adjs.append(adj)
        for adj in adjs:
            if not re.search(adj, sent.text, flags=re.I): continue
            matcher = PhraseMatcher(nlp.vocab, attr='LOWER')
            matcher.add("noun", [nlp(adj)])
            matches = matcher(sent)
            for m in matches:
                child_ = [of for of in sent[m[-2] - sent.start].children if of.dep_ == 'prep' \
                          and of.i > sent[m[-2] - sent.start].i \
                          and adj + ' ' + of.text in adj_phrase and of.lemma_ != 'to']
                if child_:
                    child_ = [prep_ for prep_ in child_ if adj + ' ' + prep_.text not in adj_phrase]
                    if not len(child_): continue
                    child_.append(sent[m[-2] - sent.start])
                    errs.append([find_span(child_),
                                 "You might want to use a different preposition with this adjective."])
        return errs

    def quantifiers(sent):
        # you may specify your own list of uncountable nouns here
        unc_list0 = []
        unc_list = unc_list0 + ['experience', 'discussion', 'effort', 'support', 'stress', 'care', 'suffering', 'crime',
                                'noise', 'trouble', 'influence', 'space']
        erroneous = []
        uncount = ['much', 'less', 'least']
        uncount_of = ['deal', 'amount', 'smidge', 'much']
        count_pl = ['many', 'few', 'fewer', 'fewest', 'several', 'various', 'numerous', 'countless']
        count_pl_special = ['these', 'those']
        count_pl_of = ['number', 'numbers', 'couple', 'dozens', 'hundreds', 'thousands', 'millions', 'billions',
                       'zillions', 'dozen', 'hundred', 'thousand', 'million', 'billion', 'zillion', 'one', 'each',
                       'every', 'either', 'neither', 'both', 'several', 'few', 'various', 'countless', 'numerous',
                       'another']
        count_sg_pl_quantified = ['each', 'every', 'another']
        uncount_count_sg = ['this', 'that', 'one']
        # needs uncountable words list to be checked
        # uncount_count_pl = ['enough'] #needs uncountable words list to be checked    uncount_count_pl_of = ['lot', 'lots', 'none', 'bags', 'heaps', 'loads', 'oodles', 'stacks']
        uncount_count_pl = ['enough']
        uncount_count_pl_of = ['lot', 'lots', 'none', 'bags',
                               'heaps', 'loads', 'oodles', 'stacks']
        quantifiers = uncount + count_pl + uncount_count_sg + uncount_count_pl
        quantifiers_of = uncount_of + count_pl_of + uncount_count_pl_of
        for i in sent:
            if i.text.lower() in quantifiers:
                if (i.text.lower() in uncount or i.text.lower() in uncount_count_sg) \
                        and 'Plur' in i.head.morph.get("Number") and i.head.pos_ == 'NOUN':
                    if i.text.lower() == 'that' and (i.pos_ == 'SCONJ' or i.dep_ != 'det'):
                        # mark
                        pass
                    elif i.text.lower() == 'one' and (i.pos_ == 'PRON' or i.dep_ != 'nummod'):

                        pass
                    else:
                        erroneous.append(
                            [find_span([i, i.head]), "Check the form of the number used with this/that/one"])
                elif i.text.lower() in count_pl and 'Sing' in i.head.morph.get("Number") \
                        and i.head.pos_ == 'NOUN':
                    erroneous.append([find_span([i, i.head]),
                                      "Check the form of the noun used with many/few/several/various/numerous/countless"])
                elif i.text.lower() in uncount_count_pl and 'Sing' in i.head.morph.get("Number") \
                        and i.head.text.lower() not in unc_list and 'NOUN' in i.head.pos_:
                    erroneous.append([find_span([i, i.head]), "Check the form of the noun used with enough"])
            elif i.text.lower() in quantifiers_of:
                for child in i.children:
                    if child.text.lower() == 'of':
                        for c in child.children:
                            if c.pos_ == 'NOUN':
                                if 'Sing' in c.morph.get("Number")[0] and i.text.lower() in count_pl_of:
                                    erroneous.append(
                                        [find_span([i, c]), 'Check the form of the noun used with number + of'])
                                elif 'Sing' in c.morph.get("Number")[0] and i.text.lower() in uncount_count_pl_of \
                                        and c.text not in unc_list:
                                    erroneous.append(
                                        [find_span([i, c]), 'Check the form of the noun used with number + of'])
                                elif 'Plur' in c.morph.get("Number")[0] and i.text.lower() in uncount_of:
                                    erroneous.append(
                                        [find_span([i, c]), 'Check the form of the noun used with number + of'])
                            elif 'ADJ' in [str(x.pos_) for x in child.children]:
                                if i.text.lower() in uncount_of:
                                    erroneous.append(
                                        [find_span([i, c]), 'Check the form of the noun used with number + of'])
            elif i.text.lower() in count_sg_pl_quantified:
                if 'NUM' not in [str(x.pos_) for x in i.head.children] \
                        and 'few' not in [str(x).lower() for x in i.head.children]:
                    if 'Plur' in i.head.morph.get("Number"):
                        erroneous.append(
                            [find_span([i, i.head]), "Check the form of the number used with each/every/another"])
            elif i.text.lower() == 'either' or i.text.lower() == 'neither':
                if 'or' not in [str(x).lower() for x in i.head.children] \
                        and 'nor' not in [str(x).lower() for x in i.head.children]:
                    if 'Plur' in i.head.morph.get("Number"):
                        erroneous.append(
                            [find_span([i, i.head]), "Check the form of the number used with either/neither"])
            elif i.text.lower() == 'both':
                children_second_level = []
                if 'and' not in [str(x).lower() for x in i.head.children] \
                        and 'ADP' not in [x.pos_ for x in i.children]:
                    for child in i.head.children:
                        children_second_level.append([str(x).lower() for x in child.children])
                    if 'and' in [item for sublist in children_second_level for item in sublist]:
                        pass
                    else:
                        if 'Sing' in i.head.morph.get("Number") and \
                                (i.head.pos_ == 'NOUN' or i.head.pos_ == 'PRON'):
                            if [find_span([i, i.head]), 'both'] not in erroneous:
                                erroneous.append([find_span([i, i.head]), 'both'])
            elif i.text.lower() in count_pl_special and i.dep_ == 'det':
                if i.head.text.lower() != 'kind' and i.head.text.lower() != 'type' \
                        and i.head.text.lower() != 'sort':
                    if 'Sing' in i.head.morph.get("Number"):
                        erroneous.append([find_span([i, i.head]), "Check the form of the number used with these/those"])
            elif i.pos_ == "NUM" and i.text.lower() != "one" and i.text != "1" \
                    and (i.head.pos_ == "NOUN" or i.head.pos_ == "ADJ"):
                if re.match(r'hundreds|thousands|millions|billions|zillions', i.head.text.lower()):
                    erroneous.append(
                        [find_span([i, i.head]), 'Check the form of the noun or noun group used with numbers'])
        return erroneous

    def polarity(sentence):
        # Checks if any polarity items were used in the wrong context
        neg_error_message = 'This item can only be used in negative contexts.'
        pos_error_message = 'This item can only be used in positive contexts.'
        polarity_errors = []

        negation = r"[Nn]['`’o]t\b|[Nn]ever(?!theless| the less)|\b[Nn]o\b|[Nn]owhere|[Nn]othing|[Nn]one|[Nn]oone|[Nn]either|"
        negation += r'[Hh]ardly|[Ss]carcely|[Bb]arely|^[Ff]ew|(?<![Aa] )[Ff]ew|[Nn]or|[Ll]ack|[Ss]top|[Aa]ny'
        ifclause = r'\b[Ii]f\b|[Ww]hether'
        negative_lic = re.compile('|'.join((negation, ifclause)))
        neg_gr = r'at all|whatsoever|just yet|yet'
        neg_exp = r'lift[a-z]{0,3} a finger|(sleep[a-z]{0,3}|slept) a wink|bat[a-z]{0,4} an eye|((takes?|took|taking)|(last[a-z]{0,3})) long\b|(drink[a-z]{0,3}|drank|drunk) a drop|(mean|small) feat'
        neg_exp += r'|put( \w+?| ) ?finger on|(thinks?|thought) much '
        temporal_neg_exp = r'in (?:hours|days|weeks(?! [0-9])|months(?! [JFMASOD])|years(?! gone| past| [a-zA-Z]*? ?[0-9])|decades|yonks|eons|a million years|ages(?! [0-9])|donkey\'s years)'
        neg_pol = re.compile('|'.join([neg_gr, neg_exp, temporal_neg_exp]))
        pos_pol = re.compile(r'already|somewhat|too')
        words = ' '.join([token.text for token in sentence])
        # When there is a negative polarity item but no prior negation
        neg = re.search(neg_pol, words)
        if sentence.text[-1] != '?' and neg:
            neg_token = None
            licensed = False
            for token in sentence:
                # Presuming if the whole NP expression is in the scope of negation then its every element will be too
                # Hence only check the first word of the NPI to match a token
                if token.text == neg.group().split()[0]:
                    neg_token = token  # technically a faulty verification, esp. with 'at all' where 'at' can be repeated later and therefore mixed up, but will have to do for now
            if neg_token:
                if (neg_token.text == 'at' and neg_token.dep_ != 'advmod') or (
                        neg_token.text == 'yet' and neg_token.head.lemma_ != 'have' and neg_token.head.dep_ != 'aux'):
                    licensed = True  # Not licensed per se, but rather not an NPI at all
                lic = re.findall(negative_lic, words)
                for l in lic:
                    for token in sentence:
                        # An NPI is licensed when it's within the scope of (i.e. c-commanded by) a negation
                        if token.text == l and (token.head.is_ancestor(neg_token) or token.is_ancestor(neg_token)):
                            licensed = True
                if not licensed:
                    polarity_errors.append([find_span([neg_token]),
                                            neg_error_message])  # if more than one word in polarity item, only finds the first one

        # todo add superlative licensing for temporal PI
        # When there is a positive polarity item but it is negated
        pos = re.search(pos_pol, words)
        if pos:
            pos_token = None
            licensed = True
            for token in sentence:
                if token.text == pos.group().split()[0]:
                    pos_token = token
            if pos_token:
                anti_lic = re.findall(negation, words)
                for al in anti_lic:
                    for token in sentence:
                        if token.text == al and token.is_ancestor(pos_token):
                            licensed = False
                if pos_token.text == 'too' and pos_token.i != len(doc) - 1:
                    if pos_token.nbor().text in ['much', 'many'] or pos_token.nbor().pos_ == 'ADJ':
                        licensed = True  # Not licensed per se, but rather not a PPI at all
                if not licensed:
                    polarity_errors.append([find_span([pos_token]), pos_error_message])
        # Checking if negation's parent is an ancestor of a PPI yields too many false positives
        return polarity_errors

    def preprocess(sentences):
        sentence_dots: str = re.sub(r'\.', '. ', sentences)
        sentence_dots = re.sub(r'\.\s\.\s\.', '...', sentence_dots)
        sentence_dots = re.sub(r'\.\s\.', '..', sentence_dots)
        sentence_dots = re.sub(r'!', '! ', sentence_dots)
        sentence_dots = re.sub(r'\?', '? ', sentence_dots)
        sentence_dots = re.sub(r'\(', ' (', sentence_dots)
        sentence_dots = re.sub(r'\)', ') ', sentence_dots)
        sentence_dots = re.sub(r'\) \.', ').', sentence_dots)
        sentence_dots = re.sub(r' ,', ',', sentence_dots)
        sentence_dots = re.sub(r'\n', ':::', sentence_dots)
        sentence_dots = re.sub(r'\s\s', ' ', sentence_dots)
        sentence_dots = re.sub(r':::', '\n', sentence_dots)
        return sentence_dots

    def apply_models(sentence_process, test_mode):
        result = []
        if test_mode:
            for sent in sentence_process.sents:
                for function in test_mode:
                    exec(f'result.append({function}(sent))')
        else:
            observed_functions = {quantifiers, past_cont, redundant_comma, hardly, that_comma, pp_time,
                                  only, inversion, extra_inversion, spelling, conditionals,
                                  consider_that, polarity, punct,
                                  agreement_s_v, gerund, prep, adj}
            apply_ = lambda f, given_: f(given_)
            for function in observed_functions:
                sentence_err = apply_(function, sentence_process)
                if sentence_err:
                    result.extend(sentence_err)
        return result

    text_ = preprocess(text)
    doc = nlp(text_)
    if test_mode:
        return apply_models(doc, test_mode)
    all_errors = dict()
    for num, sentence in enumerate(doc.sents):
        errors = apply_models(sentence, test_mode)
        if errors:
            if isinstance(errors[-1], str):
                all_errors[num] = [errors]
            else:
                all_errors[num] = errors
    return text_, all_errors


def generate_text(text):
    text_, errors = models(text)
    annotated_text, comments = output_maker(text_, errors)
    return annotated_text, comments


# nlp = spacy.load("en_core_web_sm")
# text_example = """Nowadays the number of modern devices is increasing. People are tend to spend the whole day alongside with their gadgets. According to scientific researches, modern technologies could be a great danger for modern society, especially for citizen's health.
# The first enourmous problem that can be caused by modern technologies is addiction. It affects emotional health. Consequently, a person feels nervouse without his telephone. The only possible decision is to develop a habbit to spend at least 2 or 3 hours a day without any devices.
# The second really huge problem that could be a consequence of sitting in front of a computer, smartphone or other electronic device with a screen is eyes illnesses. For instance, only 10 per cent of teenagers and young adults under the age of 25 have a good vision and no problem with eyes. One of the possible solutions is to control the time spending in front of a screen and to do special exercises for eyes. It enables to prevent eyes illnesses.
# One of the most dangerous illnesses that could appear is cancer. There was a huge research in order to demonstrate how devices affect our brains. There is an evidence that the electronic waves influence our brains and cause a cancer. The only way to predict it is to sleep at least 3 meters far from all devices and try to spend as less time with them as possible.
# To draw the conclusion, it has to be restated that modern technologies are responsible for the appearence of such awful diseases as addiction, problems with eyes and even cancer. Therefore, the only possible way to prevent these disasters is to control yourself, try to spend not more than 3 hours per day with gadgets and to do special trainings and exercises. """
# print(generate_text(text_example))
