import re
import spacy
def models(user_input):

    def preprocessing(text):

        text = re.sub(r'\n', ' ', text)
        text = re.sub(r'\s\s', ' ', text)
        text = re.sub(r'\s?:', ':', text)
        text = re.sub(r'\s?;', ';', text)
        text = re.sub(r'\s?,', ',', text)

        return text

    def pp_time(docs, errors):

        error_message = 'Present Perfect does not go along with indication of past tense.'
        for num, d in enumerate(docs.sents):
            #print(d.start)
            for token in d:
                print(token.text, token.head, token.lemma_, token.pos_, token.tag_, token.dep_,
                      token.i + d.start, token.is_oov)  # token.sent, token.is_alpha, token.is_stop , token.nbor()



            # Найти фразу, потом если глагол к ней в present perfect - ошибка

            # Если есть такие глаголы - то продолжаем
            # Поиск паттернов
            # Паттерн 1 - поиск фразы ((in\s|over\s|from\s|between\s)(the\s)?(year|years)?\d*)
            patt_one = [i for i in d if i.lemma_ in {'from', 'in', 'over', 'between'}]
            # нашли предлоги - дальше найти связи к the year/years - связь: pobj
            patt_one = [i for i in patt_one if 'year' in [j.lemma_ for j in i.children if j.dep_ == 'pobj']]
            patt_one = [i.head for i in patt_one if
                        i.head.tag_ == 'VBN']
            # have smth done prep year or (i.head.tag_ =='VBN' and i.head.head.tag_ =='VBD')
            #print('PATTERN, 1', patt_one, d)
            # Паттерн 2 - поиск фразы ((at|in|during)\s(the\s)?(first|second|third|fourth|fifth|initial|last)\\
            # \s(stage|point|phase|period|year|decade|century))
            patt_two = [i for i in d if i.lemma_ in {'at', 'in', 'during'}]

            patt_three = [i for i in d if i.lemma_ in {'ago'}]
            patt_three = [i.head for i in patt_three if i.head.tag_ == 'VBN']
            #print('PATTERN, 3', patt_three, d)
            patt_two = [i for i in patt_two if [j for j in i.children \
                                                if j.dep_ == 'pobj' and \
                                                [k for k in j.children if
                                                 k.ent_type_ == 'ORDINAL' or k.lemma_ in {'last', 'initial'}]]]

            patt_two = [i.head for i in patt_two if i.head.tag_ == 'VBN']



            patt_four = [i.head for i in d if
                         i.tag_ == 'VBN' and [j for j in i.children if j in {'year', 'term', 'summer', 'century'} \
                                              and j.dep_ == 'pobj' \
                                              and [k for k in j.children if k.lemma_ == 'last']]]


            patt_five = [i for i in d if i.lemma_ in {'from', 'since'} and \
                         i.dep_ == 'prep' and [j for j in i.children if j.tag_ == 'CD' and \
                                               not [k for k in j.children if k.dep_ == 'nmod']]]
            patt_five = [i.head for i in patt_five if i.head.tag_ == 'VBN']

            patt_six = [i for i in d if i.lemma_ == 'yesterday']
            patt_seven = [i for i in d if i.lemma_ == 'day' \
                          and [j for j in i.children if j.lemma_ == 'before' and \
                               [k for k in j.children if k.lemma_ == 'yesterday']]]
            patt_six = [i.head for i in patt_six if i.head.tag_ == 'VBN']
            patt_seven = [i.head for i in patt_seven if i.head.tag_ == 'VBN']

            # Повесить ошибку на глагол в прошедшем времени, его span добавить в поле ошибок и название ошибки
            # Span ошибки d.start + длина всех слов до в text
            all_patterns = [patt_one, patt_two, patt_three, patt_four, patt_five, patt_six, patt_seven]
            for pattern in all_patterns:
                for p in pattern:
                    flag_word = [w for w in p.children if w.lemma_ == 'have']
                    if flag_word:
                        flag_word = flag_word[0]
                        errors.append([num,[flag_word.i-d.start, p.head.i-d.start], error_message])
        return errors

    def make_extended_out(data):

        res = []
        for sent in list(data.values()):
            res.extend(sent)

        return res

    def output_maker(data, all_errors):
        created_output = [[i, '0', ''] for i in data.sents]
        result = {j:[i, '0', ''] for j,i in enumerate(data.sents)}
        if not all_errors:
            return created_output
        else:


            observed_sent = set()
            for error in all_errors:
                if error[0] not in  observed_sent:
                    observed_sent.add(error[0])

                    sentence = created_output[error[0]][0]
                    words = {i:word for i, word in enumerate(sentence)}

                    words_sequence = []
                    words_check = []
                    all_err_in_sent = [i for i in all_errors if i[0] == error[0]]
                    words_err = set()
                    for err in all_err_in_sent:
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
                        words_err = words_err|set(err[1])


                    words_sequence = sorted(words_sequence, key = lambda x: x[0])

                    sentence_no_err = []
                    explicit = set()

                    for num, token in enumerate(sentence):

                        if num not in words_err and num not in explicit:

                            if num != 0 and isinstance(sentence_no_err[-1], str):
                                t =' '
                                if re.search(r'\.|\,|\?|\!|\)|\"|\'|\`', str(token)):
                                    t = ''
                                sentence_no_err[-1] += t
                                sentence_no_err[-1] += str(token)
                            else:
                                sentence_no_err.append(str(token))
                        else:
                            errors = [err for err in words_sequence if err[0][0] == num]
                            for k in errors:
                                explicit = explicit|set(k[0])
                                sentence_no_err.append([k[0], '1', k[1]])

                    for k in range(len(sentence_no_err)):
                        element = sentence_no_err[k]
                        if isinstance(element[0], str):
                            to_replace =[element, '0', '']
                            sentence_no_err[k] = to_replace
                        else:
                            to_replace = [str(words[i]) for i in element[0]]
                            to_replace = ' '.join(to_replace)
                            sentence_no_err[k] = [to_replace, *element[1:]]
                    print(sentence_no_err)
                    result[error[0]] = sentence_no_err


        return make_extended_out(result)

    data = preprocessing(user_input)
    nlp = spacy.load("en_core_web_sm")
    doc = nlp(data)
    all_errors = []
    all_errors = pp_time(doc, all_errors)
    output = output_maker(doc, all_errors)

    return output


print(models('He has got her hair done yesterday and she has got her hair done yesterday. '
             'Also, she has got her hair done yesterday.'))


def main():
    user_input = 'She has done it yesterday. She has got it done yesterday.'

    m = models(user_input)
    print(m)



if __name__ == '__main__':
    main()