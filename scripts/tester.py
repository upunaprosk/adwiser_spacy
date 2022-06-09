from scripts.models import models
from functools import lru_cache
from tqdm import tqdm

@lru_cache(maxsize=None)
def tester(function, test_all=False):
    """
    Generates xlsx files with found mistakes
    Output file path: result/function+str(test_all) + + '.txt'

    Notes:
        First 10 found mistakes are printed
        Error if input not existing: data/function.txt or data/all_realec.txt

            Params:
                    function (str): function tested
                    test_all (bool): if False: input = data/function.txt
                                     else: input = data/all_realec.txt
    """
    functions_to_test = [function]
    if not test_all:
        file = function
    else:
        file = 'all_realec'
    txt_result = open('results/' + f'{function}' + '.txt', 'w', encoding='utf-8')
    with open('data/' + f'{file}.txt', encoding="utf-8") as file:
        all_sentences = file.readlines()
        for sentences in tqdm(all_sentences):
            for sentence in sentences.split('\n'):
                if sentence:
                    errs = models(sentence, test_mode=functions_to_test)
                    if errs:
                        if not errs[0]: continue;
                        txt_result.write(sentence + '\n')
    txt_result.close()
    return


# Possible functions to test
# observed_functions = {quantifiers, past_cont, redundant_comma, hardly, that_comma, pp_time,
#                                   only, inversion, extra_inversion, conditionals,
#                                   polarity, punct,
#                                   agreement_s_v, gerund, prep, adj}
for x in {"adj", "prep"}:
    tester(x, True)