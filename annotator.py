# 'You may have used a redundant comma in front of this conjunction.' \
# 'The usage of Past Continuous might be erroneous.'
# 'With such construction of the main clause, the next' \
# 'In if-clauses talking about unreal conditions, Past Simple or Past Perfect are expected.'
# 'Past Perfect should be used in the main clause.'    \
# 'Past Simple should be used in this clause.'   \
# 'Present Perfect does not go along with indication of time in the past.' \
# 'You may need inverted word order here.' 'You may need inverted word order here.' \
# 'You may need standard word order here.' 'You might have misspelled that word, possible '
# 'In if-clauses talking about future, Present Simple or Present Perfect are expected' \
# 'You may have used a redundant comma' \
# 'Instead of the comma, semicolon has to be used in
#
# 'You may have wrongly used the verb CONSIDER with THAT.' \
# 'That might be an erroneous use of quantifiers'

import csv
def output_maker(data, all_errors):
    def find_color(comment_string):
        with open(r'./comment-color.txt', mode='r') as csv_file:
            reader = csv.DictReader(csv_file)
            for com in reader:
                if comment_string.startswith(com['Comment']):
                    return com["HEX"]
        return '#ff8c00'
    comments = dict()
    annotated = ''
    if not all_errors:
        annotated = data
    else:
        k = 0
        iter_comment = 0
        last_interval = []
        key = None
        for _,errors in all_errors.items():
            sorted_errors = errors
            sorted_errors.sort(key=lambda tup: tup[0][-1])
            for error in sorted_errors:
                if error[0][0] >= k:
                    if error[0][0] == k:
                        annotated +=' ';
                        key = iter_comment
                    else:
                        key = iter_comment + 1
                    comments['comment' + str(key)] = error[-1]
                    annotated += data[k:error[0][0]]
                    if k-error[0][0]:
                        if error[0][0]-k >0 and data[k:error[0][0]] != '\n':
                            iter_comment+=1;

                    # comment = error[-1]
                    color = find_color(error[-1])
                    annotated += f'<div class="duo"  style="background: {color}" id="comment{iter_comment}link"'

                    annotated += ' onclick="popupbox(event,'
                    annotated += "'" + f'comment{iter_comment}' + "'" + ')"> <b>'
                    annotated += data[error[0][0]:error[0][1]]
                    annotated += '</b></div>'

                    last_interval = (error[0], key)
                    iter_comment += 1
                    k = error[0][1]
                elif error[0] == last_interval[0]:
                    value = comments['comment' + str(last_interval[1])] + '\n' + error[-1]
                    if comments['comment' + str(last_interval[1])]!= error[-1]:
                        comments['comment' + str(last_interval[1])] = value


            iter_comment += 1
        annotated += data[k: len(data)]
    return annotated.replace("\n", "<br>"), comments