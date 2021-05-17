def output_maker(data, all_errors):
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


                    annotated += f'<div class="duo" id="comment{iter_comment}link"'
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