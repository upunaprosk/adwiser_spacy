from models import models
import pandas as pd


# import tqdm

def tester(function, test_all=False):
    """
    Создает Excel таблицу с ошибками, найденными функцией в файле input.
    Путь таблицы: result/function+str(test_all) + '.xlsx'
    Путь найденных предложений с ошибками: result/function+str(test_all) + + '.txt'

    First 10 - are printed

    Note:
        Ошибка при не существовании файла input: data/function.txt или data/all_realec.txt

            Параметры:
                    function (str): Название тестируемой функции
                    test_all (bool): если False, то input = data/function.txt
                                     True -  input = data/all_realec.txt
    """
    functions_to_test = [function]
    result = pd.DataFrame(columns=['sentence', 'found_error'])
    if not test_all:
        file = function
    else:
        file = 'all_realec'
    found = 0
    out_of = 0
    txt_result = open('results/' + f'{function}{str(int(test_all))}' + '.txt', 'w', encoding='utf-8')
    with open('data/' + f'{file}.txt', encoding="utf-8") as file:
        all_sentences = file.readlines()
        counter = 0
        #for sentence in all_sentences:
        for sentence in all_sentences[:1000]:
            errs = models(sentence, functions_to_test)
            out_of += 1
            if errs:
                if not errs[0]: continue;
                found += 1
                found_sentences = sentence
                if found: found_sentences += '\n';
                if found <= 10:
                    print(sentence)
                txt_result.write(found_sentences)
                result.loc[result.shape[0] + 1, 'sentence'] = str(sentence)
                result.loc[result.shape[0] + 1, 'found_error'] = str(errs)
            counter += 1
            if counter%500: print('Processed:', counter);
    txt_result.close()
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

tester('inversion', True)

