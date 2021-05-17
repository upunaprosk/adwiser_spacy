import spacy
from autocorrect import Speller
from spacy.tokens import Token
from annotator import output_maker
from spacy.matcher import DependencyMatcher
from spacy.matcher import Matcher

char_span = lambda token: (token.idx, token.idx + len(token.text))
Token.set_extension(name='span', getter=char_span)


def find_span(tokens):
    if len(tokens) == 1:
        token = tokens[0]
        print(token)
        return [token._.span[0], token._.span[1]]
    ss = min([s._.span[0] for s in tokens])
    s: Token
    sm = max([s._.span[1] for s in tokens])
    return [ss, sm]


def without_child(token, values):
    wrong_keys = {'dep', 'lemma', 'norm', 'tag', 'pos'}
    construct_pattern = '[i for i in token.children if '
    for value in values.keys():
        if value not in dir(token) or value in wrong_keys:
            raise AttributeError(f'Invalid attribute {value}')
        temp = 'i.' + value
        if isinstance(values[value], list):
            temp_2 = '{' + str(values[value])[1:-1] + '}'
            temp += ' in '
            temp += temp_2
        elif isinstance(values[value], str):
            temp += ' == ' + '\'' + str(values[value]) + '\''
        else:
            raise KeyError(f'Invalid key: {type(values[value])}')
        temp += ' and '
        construct_pattern += temp
    construct_pattern = construct_pattern[:-5] + ']'
    try:
        flag = exec(construct_pattern)
        if flag: return False
    except:
        raise KeyError(f'Invalid key')
    return True

def models(text, test_mode=False):
    def pp_time(sent):

        errors_pp = []
        all_errors = []
        dep_matcher = DependencyMatcher(vocab=nlp.vocab)
        present_perfect = [{'RIGHT_ID': 'verb', 'RIGHT_ATTRS': {'TAG': 'VBN'}},
                           {'LEFT_ID': 'verb', 'REL_OP': '>', 'RIGHT_ID': 'have',
                            'RIGHT_ATTRS': {'LEMMA': 'have', 'DEP': 'aux', 'TAG': {'IN': ['VBP', 'VBZ']}}}]
        dep_matcher.add("present_perfect", patterns=[present_perfect])
        results = dep_matcher(sent)
        if results:

            error_message = 'Present Perfect does not go along with indication of past tense.'
            all_matches = []
            verbs = []
            dep_matcher_ = DependencyMatcher(vocab=nlp.vocab)

            # in/from/over/between+CD
            patt_one = [{'RIGHT_ID': 'prep', 'RIGHT_ATTRS': {'LEMMA': {'IN': ['from', 'in', 'over', 'between']}}},
                        {'LEFT_ID': 'prep', 'REL_OP': '>', 'RIGHT_ID': 'year',
                         'RIGHT_ATTRS': {'TAG': 'CD', 'DEP': 'pobj'}}]

            dep_matcher_.add('prep+cd', patterns=[patt_one])
            dep_matches = dep_matcher_(sent)

            # + у последнего нет детей с леммой recent/last!!!
            if dep_matches and without_child(sent[dep_matches[0][1][1]], {'lemma_': ['last', 'recent']}):
                all_matches.append(dep_matches[0][1][0])
                if sent[dep_matches[0][1][0]].head.tag_ == 'VBN':
                    verbs.append(sent[dep_matches[0][1][0]].head)
            # in/from/over/between+year
            patt_two = [{'RIGHT_ID': 'prep', 'RIGHT_ATTRS': {'LEMMA': {'IN': ['at', 'over', 'in']}}},
                        {'LEFT_ID': 'prep', 'REL_OP': '>', 'RIGHT_ID': 'year',
                         'RIGHT_ATTRS': {'LEMMA': 'year', 'DEP': 'pobj'}}]

            dep_matcher_.add('prep+year', patterns=[patt_two])
            # at/in/over + last/recent + NN
            patt_three = [{'RIGHT_ID': 'prep', 'RIGHT_ATTRS': {'LEMMA': {'IN': ['at', 'over', 'in']}}},
                          {'LEFT_ID': 'prep', 'REL_OP': '>', 'RIGHT_ID': 'noun',
                           'RIGHT_ATTRS': {'TAG': 'NN', 'DEP': {'IN': ['pobj', 'npadvmod']}}},
                          {'LEFT_ID': 'noun', 'REL_OP': '>', 'RIGHT_ID': 'adj',
                           'RIGHT_ATTRS': {'LEMMA': {'IN': ['last', 'initial']}}}]

            dep_matcher_.add('prep+noun+last/initial', patterns=[patt_three])
            # at/in/over + ordinal + NN
            patt_four = [{'RIGHT_ID': 'prep', 'RIGHT_ATTRS': {'LEMMA': {'IN': ['at', 'over', 'in']}}},
                         {'LEFT_ID': 'prep', 'REL_OP': '>', 'RIGHT_ID': 'noun',
                          'RIGHT_ATTRS': {'TAG': 'NN', 'DEP': {'IN': ['pobj', 'npadvmod']}}},
                         {'LEFT_ID': 'noun', 'REL_OP': '>', 'RIGHT_ID': 'ord_adj',
                          'RIGHT_ATTRS': {'ENT_TYPE': 'ORDINAL'}}]

            dep_matcher_.add('prep+noun+ordinal', patterns=[patt_four])
            # ago (but not since a long ago)
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
            # поиск verbs
            if dep_matcher_(sent):
                for match_dep in dep_matcher_(sent):
                    if sent[match_dep[1][0]].head.tag_ == 'VBN':
                        verbs.append(sent[match_dep[1][0]].head)
                    if nlp.vocab[match_dep[0]].text == 'since_1998_to_2000':
                        if sent[match_dep[1][1]].lemma_ == 'since':
                            tok = sent[match_dep[1][1]]
                            all_errors.append([find_span([tok]),
                                              'You may have used \'since\' instead of \'from\''])

            # теперь have + not от каждого глагола + ошибки
            for verb in verbs:
                if verb.tag_ == 'VBN':

                    have_not = [have for have in verb.children if have.lemma_ == 'have' and have.dep_ == 'aux']
                    if have_not:
                        have_not = have_not[0]
                        errors_pp.append(have_not)
                        not_ = [i for i in have_not.children if i.dep_ == 'neg' and i.norm_ == 'not']
                        if not_:
                            errors_pp.append(not_)
                        all_errors.append([find_span(errors_pp), error_message])
        return all_errors

    def inversion(sent):

        error_message = 'This might be an erroneous use of inversion.'

        def find_wrong_order(token_i):

            possible_inversions = {'barely', 'never', 'rarely', 'hardly', 'seldom',
                                   'scarcely', 'nowhere', 'neither', 'nor'}
            if token_i.lemma_ in possible_inversions:
                return True
            elif token_i.lemma_ == 'little' and token_i.dep_ in {'npadvmod', 'dobj', 'advmod'}:
                if without_child(token_i, {'lemma_': 'by'}):
                    return True
            elif token_i.lemma_ == 'not':
                flag = [i for i in token_i.children if i.lemma_ in {'only', 'until'}]
                if flag:
                    return  True

            return False

        for token in sent:  # for future modifications
            flag = False
            if not (token.i - sent.start):
                prep_no_noun = [{'RIGHT_ID': 'prep',
                                 'RIGHT_ATTRS': {'LEMMA': {'IN': ['under', 'in', 'over', 'at', 'for', 'to', 'with']},
                                                 'TAG': 'IN'}},
                                {'LEFT_ID': 'prep', 'REL_OP': '>', 'RIGHT_ID': 'noun', 'RIGHT_ID': 'noun',
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

                    verb = token.head if token.head.pos_ == 'AUX' else ''
                    if not verb:
                        aux = [v for v in token.head.children if v.pos_ == 'AUX']
                        verb_ = token.head if token.head.pos_ == 'VERB' else ''
                        aux_s = [v for v in token.head.head.children if v.pos_ == 'AUX']
                        if aux:
                            verb = aux[0]
                        elif aux_s:
                            verb = aux_s[0]
                        elif verb_:
                            verb = verb_

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

        error_message = 'This might be an erroneous use of inversion.'

        only_1 = [{'RIGHT_ID': 'only', 'RIGHT_ATTRS': {'LEMMA': 'only', 'DEP': 'advmod'}},
                  {'LEFT_ID': 'only', 'REL_OP': '<', 'RIGHT_ID': 'advcl', 'RIGHT_ATTRS': {'TAG': 'WRB'}},
                  {'LEFT_ID': 'advcl', 'REL_OP': '$++', 'RIGHT_ID': 'verb', 'RIGHT_ATTRS': {'DEP': 'ccomp'}},
                  {'LEFT_ID': 'verb', 'REL_OP': '>', 'RIGHT_ID': 'noun',
                   'RIGHT_ATTRS': {'DEP': {'IN': ['nsubj', 'nsubjpass']}}}]

        only_1_2 = [{'RIGHT_ID': 'only', 'RIGHT_ATTRS': {'LEMMA': 'only', 'DEP': 'advmod'}},
                    {'LEFT_ID': 'only', 'REL_OP': '<<', 'RIGHT_ID': 'advcl', 'RIGHT_ATTRS': {'DEP': 'advcl'}},
                    {'LEFT_ID': 'advcl', 'REL_OP': '<', 'RIGHT_ID': 'verb', 'RIGHT_ATTRS': {'POS': 'VERB'}},
                    {'LEFT_ID': 'verb', 'REL_OP': '>', 'RIGHT_ID': 'noun',
                     'RIGHT_ATTRS': {'DEP': {'IN': ['nsubj', 'nsubjpass']}}}]

        dep_matcher_ = DependencyMatcher(vocab=nlp.vocab)
        dep_matcher_.add('only_1', patterns=[only_1, only_1_2])

        verb_start = None
        noun = None
        if dep_matcher_(sent):
            verb_start = sent[dep_matcher_(sent)[0][1][-2]]
            noun = sent[dep_matcher_(sent)[0][1][-1]]
        elif sent[0].lemma_ == 'only' and sent[0].dep_ == 'advmod':
            verbs = {}
            matcher_only = Matcher(vocab=nlp.vocab)
            matcher_only.add('verb', patterns=[[{'POS': 'VERB'}]])
            if len(matcher_only(sent)) == 1:
                verb_start = sent[matcher_only(sent)[0][1]]
                noun = [n for n in verb_start.children if n.dep_ in ['nsubj', 'nsubjpass']]
                if noun:
                    noun = noun[0]
        if noun and verb_start:
            aux_ = [aux for aux in verb_start.children if aux.pos_ == 'AUX']
            if aux_:
                verb_start = aux_[0]
            if verb_start.i > noun.i:
                err = [[find_span([verb_start]), error_message]]
                return err
        return

    def extra_inversion(sent):

        error_message = 'This might me an erroneous use of inversion.'
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
                            words = [sent[k] for k in range(aux[0].i, noun[0].i + 1)]
                            return ([find_span(words), error_message])
            return


    def spelling(sent):
        spell = Speller(lang='en')
        errors = []
        for token in sent:
            print('SPELLING',spell(str(token.text)) )
            if str(spell(str(token.text))) != str(token.text):
                errors.append([find_span([token]),
                               f'You might have misspelled that word, possible '
                               f'correction: {str(spell(str(token.text)))}'])
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
        if dep_matcher_(sent):

            matched = nlp.vocab[dep_matcher_(sent)[0][0]]
            errors = []
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
                                   f'In such construction of the main clause, the following ones should start with {allowed}.'])

                if not (sent[dep_matcher_(sent)[0][1][0]].tag_ == 'VBN' and [aux for aux in sent[dep_matcher_(sent)[0][1][0]].children if
                                                     aux.dep_ == 'aux' and aux.pos_ == 'VBD' and aux.lemma_ == 'have']):
                    errors.append([find_span([sent[dep_matcher_(sent)[0][1][0]]]), 'Past Perfect should be used in the main clause.'])
                for clause in advcls:
                    verb = clause

                    if not (verb.tag_ == 'VBD' and without_child(verb, {'pos_': 'AUX', 'dep_': 'aux'})):
                        errors.append([find_span([verb]), 'Past Simple should be used in that clause.'])
            return errors

    def conditionals(sent):

        if [x for x in sent if x.lemma_ in {'whether', 'if'}]:
            root = sent.root if sent.root.pos_ == 'VERB' else ''
            if root:
                errors = []
                will = [x for x in root.children if x.dep_ == 'aux' and x.lemma_ == 'will']
                would = [x for x in root.children if x.dep_ == 'aux' and x.lemma_ == 'would']
                advcls = [x for x in sent if x.dep_ == 'advcl' and [y for y in x.children if
                                                                    y.lemma_ in {'whether', 'if'} and y.dep_ == 'mark']]
                for advcl in advcls:

                    ss = 'http://realec-reference.site/viewArticle/CONDITIONAL%20SENTENCES'
                    will_if_clause = [x for x in advcl.children if x.dep_ == 'aux' and x.lemma_ in {'will', 'would'}]

                    if will_if_clause:
                        errors.append([find_span([will_if_clause[0]]),
                                       'In the conditional part of the conditional sentence \'will\' and \'would\' cannot be used.'])
                    verb = advcl
                    if will:

                        have = [have for have in verb.children if
                                (have.lemma_ == 'have' and have.dep_ == 'aux' and have.tag_ in {'VBP', 'VBZ'})]
                        pres_perfect = True if verb.tag_ == 'VBN' and have else False
                        pres_simple = True if verb.tag_ in {'VB','VBP', 'VBZ'} else False
                        if not (pres_perfect | pres_simple):
                            errors.append([find_span([verb]),
                                           'In the if-clause of the sentence (Talking about future) Present Simple or Present Perfect are expected. (More examples: http://realec-reference.site/viewArticle/CONDITIONAL%20SENTENCES )'])

                    elif would:
                        past_perfect = True if verb.tag_ == 'VBN' \
                                               and [have for have in verb.children if have.dep_ == 'aux' \
                                                    and have.text == 'had'] else False
                        past_simple = True if verb.tag_ == 'VBD' \
                                              and without_child(verb, {'dep_': 'aux'}) else False

                        if not (past_perfect | past_simple):
                            errors.append([find_span([verb]),
                                           r'In the if-clause of the sentence (Talking about past) Past Simple or Past Perfect are expected.(More examples: http://realec-reference.site/viewArticle/CONDITIONAL%20SENTENCES) '])

                return errors

    def that_comma(sent):

        error_that = DependencyMatcher(vocab=nlp.vocab)
        comma_that = [{'RIGHT_ID': 'comma', 'RIGHT_ATTRS': {"LEMMA": ",", "POS": "PUNCT"}},
                      {'LEFT_ID': 'comma', 'REL_OP': '.', 'RIGHT_ID': 'that', 'RIGHT_ATTRS': {'LEMMA': 'that'}}]
        error_that.add('comma_that', [comma_that])
        if error_that(sent):
            errors = []
            for match in error_that(sent):
                that = sent[match[1][-1]]
                if that.dep_ in {'nsubj', 'nsubjpass'}:
                    errors.append([find_span([sent[match[1][0]], that]),
                                   'Instead of the comma semicolon has to be used in that case.'])
            first_that = sent[error_that(sent)[0][1][-1]]
            if first_that.dep_ == 'mark':
                errors.append([find_span([sent[error_that(sent)[0][1][0]], first_that]),
                               'You may have used a redundant comma in this sentence.'])
            return errors
        return

    def punct(sent):
        pass

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
                first = False
                errors.append([find_span([sent[match[1][-1]], sent[match[1][-2]]]),
                               'You may have used a redundant comma in this sentence.'])
        return errors

    def past_cont(sent):
        p_cont = [{'RIGHT_ID': 'vbg', 'RIGHT_ATTRS': {'TAG': 'VBG'}},
                  {'LEFT_ID': 'vbg', 'REL_OP': '>', 'RIGHT_ID': 'was', 'RIGHT_ATTRS': {'DEP': 'aux', 'TAG': 'VBD'}}]
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
                            and while_.lemma_ in {'as', 'while'} for while_ in advcl.children]): while_ = True;break;

                if not while_ or errors:
                    errors.append([find_span([sent[match[1][1]], sent[match[1][0]]]),
                                   'The usage of Past Continuous might be erroneous.'])

            return errors

        return

    def captization(sent):

        pass

    def agreement_s_v(sent):
        pass

    def prep(sent):
        pass

    def adj(sent):
        pass

    def quantifiers(sent):
        pass

    def polarity(sent):
        pass

    def apply_models(sentence, test_mode):
        result = []
        if test_mode:
            for function in test_mode:
                exec(f'result.append({function}(sentence))')

        else:
            observed_functions = {past_cont, redundant_comma, hardly, that_comma,
                      pp_time, only, inversion, extra_inversion, spelling, conditionals}


            apply_ = lambda f, given_: f(given_)
            for function in observed_functions:
                sentence_err = apply_(function, sentence)
                if sentence_err:
                    result.extend(sentence_err)
        return result

    nlp = spacy.load("en_core_web_sm")
    doc = nlp(text)
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

    return all_errors


def generate_text(text):
    errors = models(text)
    annotated_text, comments = output_maker(text, errors)
    return annotated_text, comments
