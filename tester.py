
from models import models
import pandas as pd
from tqdm import tqdm

def tester(function, test_all = False):
    '''
    Создает Excel таблицу с ошибками, найденными функцией в файле input.
    Путь таблицы: result/function+str(test_all) + '.xlsx'

    Note:
        Ошибка при не существовании файла input

            Параметры:
                    function (str): Название тестируемой функции
                    test_all (bool): если False, то input = data/function.txt
                                     True -  input = data/all_realec.txt
    '''
    functions_to_test = [function]
    result = pd.DataFrame(columns=['sentence', 'found_error'])
    if not test_all:
        file = function
    else:
        file = 'all_realec'
    found = 0
    out_of = 0
    with open('data/' + f'{file}.txt', encoding="utf-8") as file:
        all_sentences = file.readlines()
        while found <= 10:
            for num, sentence in enumerate(tqdm(all_sentences)):
                errs = models(sentence, functions_to_test)
                out_of +=1
                if errs:
                    if isinstance(errs[0], list) and len(errs[0]) <=1: continue;
                    found+=1
                    result.loc[num, 'sentence'] = str(sentence)
                    result.loc[num, 'found_error'] = str(errs)
                    if found >= 1:
                        break
    result.to_excel('results/' + f'{function}{str(int(test_all))}' + '.xlsx')
    if not test_all:
        print(f'Found: {found} out of {out_of}')
    return



# tester - принимает строковое название функции function (можно несколько)
# и bool переменную (True при отлавливании ошибок на всех предложениях,
# False - файле data/function.txt (для собственно-придуманных примеров)
# Результат - записывается в папку results/function.xlsx

# observed_functions = {past_cont, redundant_comma, hardly, that_comma,
#                       pp_time, spelling, only, inversion, extra_inversion, spelling, conditionals}
# Доступные функции для теста в множестве выше

tester('pp_time',  True)