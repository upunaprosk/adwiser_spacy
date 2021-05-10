import re
import spacy
from autocorrect import Speller

nlp = spacy.load("en_core_web_sm")


# TODO add without attribute as token attrs by set_extension for expanding DepMatcher
def models(user_input):
    def preprocessing(text):
        # seems no need in it..

        return text

    # TODO add Spacy Matchers for pp_time
    def pp_time(docs, errors):

        error_message = 'Present Perfect does not go along with indication of past tense.'
        for num, d in enumerate(docs.sents):

            patt_one= [i for i in d if i.lemma_ in {'from', 'in', 'over', 'between'}]
            patt_one = [i.head for i in patt_one if ([j for j in i.children if
                                                      j.dep_ == 'pobj' and j.lemma_ == 'year' and not [rec for rec in
                                                                                                       j.children if
                                                                                                       rec.lemma_ in {
                                                                                                           'recent',
                                                                                                           'last'}]] \
                                                     or [j for j in i.children if j.tag_ == 'CD'])]

            patt_one = [i for i in patt_one if
                        i.tag_ == 'VBN']

            #
            periods = {'year', 'term', 'week', 'semester', 'century' \
                                                           'day', 'month', 'decade', 'spring', 'fall',
                       'autumn', 'winter', 'summer', 'night',
                       'evening', 'morning', 'season', 'stage', 'point', 'phase'
                       }
            patt_two = [i for i in d if i.lemma_ in {'at', 'in', 'over'}]
            patt_two = [i for i in patt_two if [j for j in i.children \
                                                if j.dep_ in {'pobj', 'npadvmod'} and j.tag_ == 'NN' and \
                                                [k for k in j.children if
                                                 k.ent_type_ == 'ORDINAL' or \
                                                 k.lemma_ in {'last', 'initial'}]]]
            patt_two = [i.head for i in patt_two if i.head.tag_ == 'VBN']

            patt_three = [i for i in d if i.lemma_ in {'ago'}]
            patt_three = [i.head for i in patt_three if i.head.tag_ == 'VBN' and not [k for k in \
                                                                                      i.head.children \
                                                                                      if k.lemma_ == 'since']]

            patt_four = [i for i in d if
                         i.tag_ == 'VBN' and [j for j in i.children if j in periods \
                                              and j.dep_ in {'pobj', 'npadvmod'} and j.tag_ == 'NN'
                                              and [k for k in j.children if k.lemma_ == 'last']]]

            patt_five = [i.head for i in d if i.lemma_ in {'from', 'since'} and \
                         i.dep_ == 'prep' and [j for j in i.children if j.tag_ == 'CD' and \
                                               not [k for k in j.children if k.dep_ == 'nmod']]]
            patt_five = [i for i in patt_five if [n for n in i.children if n.lemma_ == 'to' and \
                                                  n.dep_ == 'prep' and [j for j in n.children if j.tag_ == 'CD' and \
                                                                        not [k for k in j.children if
                                                                             k.dep_ == 'nmod']]]]
            patt_five = [i for i in patt_five if i.head.tag_ == 'VBN']

            patt_six = [i for i in d if i.lemma_ == 'yesterday']
            patt_seven = [i for i in d if i.lemma_ == 'day' \
                          and [j for j in i.children if j.lemma_ == 'before' and \
                               [k for k in j.children if k.lemma_ == 'yesterday']]]
            patt_six = [i.head for i in patt_six if i.head.tag_ == 'VBN']
            patt_seven = [i.head for i in patt_seven if i.head.tag_ == 'VBN']

            basic_last = [i for i in d if i.tag_ == 'VBN' \
                          and [j for j in i.children if j.pos_ == 'NOUN' and j.head.dep_ != 'prep' and \
                               [k for k in j.children if k.lemma_ == 'last']
                               ]]
            all_patterns = [patt_one, patt_two, patt_three, \
                            patt_four, patt_five, patt_six, patt_seven, basic_last]
            errs = set()
            for pattern in all_patterns:
                for p in pattern:
                    flag_word = [w for w in p.children if w.lemma_ == 'have' and w.dep_ == 'aux']
                    if flag_word:
                        flag_word = flag_word[0]
                        if not {flag_word.i - d.start}.intersection(errs):
                            errs = errs | {flag_word.i - d.start}
                            not_ = [i for i in p.children if i.dep_ == 'neg' and i.lemma_ == 'not']
                            span = [flag_word.i - d.start]
                            if not_:
                                span.append(not_[0].i - d.start)

                            errors.append([num, span, error_message])
        return errors

    def inversion(docs, errors):
        error_message = 'This might be an erroneous use of inversion.'

        def find_wrong_order(token_i):
            possible_inversions = {'barely', 'never', 'rarely', 'hardly', 'seldom',
                                   'scarcely'}
            if token_i.lemma_ in possible_inversions:
                return True
            elif token_i.lemma_ == 'under':
                flag = [i for i in token_i.children if i.lemma_ == 'circumstances']
                if flag:
                    if {i for i in token_i.children if i.lemma_ == 'no'}:
                        return True
            elif token_i.lemma_ == 'no':
                flag = [i for i in token_i.children if i.lemma_ == 'sooner']
                if flag:
                    return True
            elif token_i.lemma_ == 'not':
                flag = [i for i in token_i.children if i.lemma_ in {'only', 'until'}]
                if flag:
                    return True
            elif token_i.lemma_ == 'at':
                flag = [i for i in token_i.children if i.lemma_ in {'no'}]
                if {i for i in token_i.children if i.lemma_ in {'time', 'point'}}:
                    return True

            elif token_i.lemma_ == 'little' and token_i.dep_ in {'npadvmod', 'dobj'}:
                if not [i for i in token_i.children if i.lemma_ in {'by'}]:
                    return True

            return False

        for num, d in enumerate(docs.sents):

            for token in d:
                if not (token.i - d.start):
                    if find_wrong_order(token):
                        verb = token.head if token.head.pos_ == 'AUX' else ''
                        wrong_order = False
                        if not verb:
                            aux = [v for v in token.head.children if v.pos_ == 'AUX']
                            verb_ = token.head if token.head.pos_ == 'VERB' else ''
                            if aux:
                                verb = aux[0]
                            elif verb_:
                                verb = verb_
                        if verb:
                            noun = [noun for noun in token.head.children if noun.dep_ == 'nsubj']
                            wrong_order = False
                            if noun:
                                wrong_order = True if verb.i > noun[0].i else False
                                if wrong_order:
                                    errors.append([num, [verb.i - d.start], error_message])

        return errors

    def extra_inversion(docs, errors):
        error_message = 'This might me an erroneous use of inversion.'
        for num, d in enumerate(docs.sents):
            verb = d.root
            cite = [i for i in verb.children if i in {'"', '\'', '\`'}]
            if not cite:
                ccomp_verb = [i for i in verb.children if i.dep_ == 'ccomp' \
                              and i.pos_ == 'VERB']
                wrb = ''
                if ccomp_verb:

                    wrb = [i for i in ccomp_verb[0].children if i.tag_ == 'WRB' and i.dep_ == 'advmod']
                    if not wrb:
                        whether = [i for i in ccomp_verb[0].children if i.pos_ == 'SCONJ' \
                                   and i.dep_ == 'mark' and i.lemma_ in {'if', 'whether'}]
                        if whether:
                            wrb = whether

                    if wrb:
                        aux = [i for i in ccomp_verb[0].children if i.dep_ == 'aux' \
                               and i.pos_ == 'AUX']
                        noun = [i for i in ccomp_verb[0].children if i.dep_ == 'nsubj']
                        if not aux:
                            aux = ccomp_verb
                        if noun and aux:
                            if aux[0].i < noun[0].i:
                                words = range(aux[0].i, noun[0].i + 1)
                                errors.append([num, [*words], error_message])
                return errors

    def make_extended_out(data):

        res = []
        for sent in list(data.values()):

            if isinstance(sent[0], str):
                res.append(sent)
                continue
            res.extend(list(sent))

        for i, _ in enumerate(res):
            res[i][0] = res[i][0].replace('\r\n ', '\r\n')
        return res

    misspelled_words = set()

    def spelling(docs, errors):
        spell = Speller(lang='en')
        for num, d in enumerate(docs.sents):
            for token in d:
                if str(spell(str(token.text))) != str(token.text):
                    misspelled_words.add(str(token.text).lower())
                    errors.append([num, [token.i - d.start],
                                   f'You might have misspelled that word, possible correction: {str(spell(str(token.text)))}'])
        return errors

    def capitilise_error(sentence, nums):
        if not nums:
            return []
        nums = set(nums)
        text_ = preprocessing(sentence)
        docs_ = nlp(text_)
        errors = set()
        for d in docs_.sents:
            for t in d:
                if t.i in nums:
                    if t.pos_ in {'PROPN'}:

                        if t.ent_type_ in {'GPE', \
                                           'LANGUAGE', 'DATE', 'PERSON', 'EVENT'} and \
                                str(t.lemma_).lower() not in misspelled_words:
                            errors.add(t.i)
                        elif t.lemma_ in {'Microsoft', 'Google', 'Apple', 'Facebook'}:
                            errors.add(t.i)
        return errors

    def capitalize(docs, errors):
        for num, d in enumerate(docs.sents):
            string = ''
            length = d.end - d.start
            possible_errs = []
            for token in d:
                if (str(token.pos_) == 'NOUN' or (len(str(token.text)) in {2, 3, 4})) and token.lemma_ not in {'my',
                                                                                                               'nail',
                                                                                                               'kid'}:

                    possible_errs.append(token.i - d.start)
                    ttt = str(token.text).capitalize()
                    if len(str(token.text)) <= 4 and ttt not in {'New', 'San'}:
                        ttt = ttt.upper()
                    string += ttt
                else:
                    if str(token.pos_) == 'PRON' and \
                            token.lemma_ == 'I' and not token.is_title:
                        errors.append([num, [token.i - d.start], 'You should capitilize that word.'])
                    elif str(token.pos_) == 'NNP' and not token.is_title:
                        errors.append([num, [token.i - d.start], 'You should capitilize that word.'])
                    string += token.text
                if token.i - d.start < length - 1:
                    string += ' '
            possible_errs = set(possible_errs)
            more_errs = capitilise_error(string, possible_errs)
            errs = possible_errs & set(more_errs)
            if errs:
                errors.append([num, list(errs), f'You should probably capitilize that word.'])
        return errors

    def output_maker(data, all_errors):

        created_output = [[i, '0', ''] for i in data.sents]
        result = {j: [str(i), '0', ''] for j, i in enumerate(data.sents)}
        if not all_errors:
            return created_output
        else:
            observed_sent = set()
            for error in all_errors:
                if error[0] not in observed_sent:
                    observed_sent.add(error[0])
                    sentence = created_output[error[0]][0]
                    words = {i: word for i, word in enumerate(sentence)}
                    words_sequence = []
                    # all errors of the sentence
                    all_err_in_sent = [i for i in all_errors if i[0] == error[0]]

                    words_err = set()
                    for err in all_err_in_sent:
                        # index of the word
                        index_word = len(err[1]) - 1
                        while (index_word >= 0):
                            temp = set()
                            temp.add(err[1][index_word])
                            flag = err[1][index_word] - err[1][index_word - 1] == 1
                            while (flag):
                                temp.add(err[1][index_word - 1])
                                index_word -= 1
                                flag = err[1][index_word] - err[1][index_word - 1] == 1
                            else:
                                index_word -= 1

                            add = [list(temp), err[2]]

                            words_sequence.append(add)
                        words_err = words_err | set(err[1])

                    words_sequence = sorted(words_sequence, key=lambda x: x[0])

                    sentence_no_err = []
                    explicit = set()
                    quotes = 0
                    # suppose no errors in quotes
                    for num, token in enumerate(sentence):

                        if num not in words_err and num not in explicit:
                            punct = False
                            if num != 0 and isinstance(sentence_no_err[-1], str):
                                t = ' '

                                if re.search(r'^(\.|\,|\?|\!|\)|-|–|—|:|;|%|\')', str(token)):

                                    punct = True
                                    t = ''
                                else:
                                    if token.is_quote:
                                        if not quotes % 2:
                                            t = ' '
                                        else:
                                            t = ''
                                    if re.search(r'-|–|—|\(|\=', str(sentence_no_err[-1][-1])):
                                        t = ''
                                    if re.search(r'\"|\'|\`', str(sentence_no_err[-1][-1])):
                                        if quotes + 1 % 2: t = '';

                                sentence_no_err[-1] += t
                                sentence_no_err[-1] += str(token)
                            else:
                                sentence_no_err.append(str(token))
                        else:
                            errors = [err for err in words_sequence if err[0][0] == num]
                            for k in errors:
                                explicit = explicit | set(k[0])
                                sentence_no_err.append([k[0], '1', k[1]])
                        if token.is_quote:
                            quotes += 1

                    for k in range(len(sentence_no_err)):
                        element = sentence_no_err[k]
                        if isinstance(element[0], str):
                            to_replace = [str(element), '0', '']
                            sentence_no_err[k] = to_replace
                        else:
                            to_replace = [str(words[i]) for i in sorted(element[0])]
                            to_rep = '' + to_replace[0]
                            for word in to_replace[1:]:
                                t = ' '
                                if re.search(r'^(\.|\,|\?|\!|\)|-|–|—|\:|\;)', str(word)):
                                    t = ''
                                to_rep += t
                                to_rep += word
                            to_replace = to_rep
                            sentence_no_err[k] = [to_replace, *element[1:]]

                    for ii, s in enumerate(sentence_no_err):

                        if ii not in {0, len(sentence_no_err) - 1} and str(s[1]) == '1':
                            start = ' '
                            end = ' '
                            # case of punct token
                            if re.search(r'^(,|\.|\)|\?|\!|\:|\s,)', str(s[0])):
                                start = ''
                            # case of punct token
                            if re.search(r'^(\(|:|\.|\,)', str(sentence_no_err[ii + 1][0])):
                                end = ''
                            sentence_no_err[ii - 1][0] += start
                            nnn = end + str(sentence_no_err[ii + 1][0])
                            if end:
                                print('sentence_no_err[ii + 1][0]', sentence_no_err[ii + 1][0])
                                print(sentence_no_err[ii + 1][0])
                            sentence_no_err[ii + 1][0] = nnn

                    xx = sentence_no_err[-1][0]
                    if xx.rstrip() == xx:
                        xx += ' '
                        sentence_no_err[-1][0] = xx
                    result_final = [i for i in sentence_no_err if isinstance(i, list)]
                    result[error[0]] = result_final

        return make_extended_out(result)

    data = preprocessing(user_input)
    doc = nlp(data)
    all_errors = []
    all_errors = pp_time(doc, all_errors)
    all_errors = inversion(doc, all_errors)
    all_errors = extra_inversion(doc, all_errors)
    all_errors = spelling(doc, all_errors)
    # all_errors = capitalize(doc, all_errors)
    output = output_maker(doc, all_errors)

    return output


text1= 'According to the statistic presented by ITMO , who has such situation on the faculty of economics a lot of people lost their study places due to this experiment and as a resulted only few students who studied in these groups were satisfied with such situation.'
print(models(text1))
