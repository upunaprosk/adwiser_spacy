from spacy.tokens import Token

char_span = lambda token: (token.idx, token.idx + len(token.text))
Token.set_extension(name='span', getter=char_span)

def find_span(tokens):
    if len(tokens) == 1:
        token = tokens[0]
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
        flag = eval(construct_pattern)
        if flag: return False
    except:

        raise KeyError(f'Invalid key')
    return True
