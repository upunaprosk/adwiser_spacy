from flask import Flask, Markup, request, render_template
from models import models


def annotate(text):
  ann_strings = models(text)
  print('text',ann_strings)

  tokens_soup = []
  comments = {}
  k = 0
  for i, ann in enumerate(ann_strings):
      print('ANNOTATION', ann)
      tokens_soup.append([str(ann[0]), int(ann[1])])
      if ann[2]:
          comments["comment" + str(i)] = ann[2]

  print(tokens_soup, comments);
  return tokens_soup, comments


def annotate_print(text):
    tokens_soup, comments = annotate(text)
    for token in tokens_soup:
         text = text.replace(token[0], chr(8), 1)
    for k, token in enumerate(tokens_soup):
        entry = ""
        if token[1] == 1:
            entry += '<div class="duo"'
            print("comment" + str(k), 'NOT IN', comments)
            print("tokens_soup", tokens_soup, 'token', token)

            if "comment"+str(k) in comments:
                entry += ' id="' + "comment"+str(k) + 'link"'
                entry += ' onclick="popupbox(event,'
                entry += "'" + "comment"+str(k) + "'" + ')">'
            else:
            	entry += '>'
        entry += token[0]

        if token[1] == 1:
            entry += '</div>'
        text = text.replace(chr(8), entry, 1)
    text = text.replace("\n", "<br>")
    print('FINAL TEXT', text)
    return text, comments

app = Flask(__name__)

@app.route('/')
def index():
    if request.args:
        text_to_inspect = request.args['text_to_inspect']
        annotation, comments = annotate_print(text_to_inspect)
        print('2222222222', annotation, comments);
        annotation = Markup(annotation)
        return render_template("result.html", annotation=annotation, comments=comments)
    return render_template("main.html")

if __name__ == '__main__':

    app.run(debug = True)
    #port = int(os.environ.get("PORT", 5000))
    #app.run(host='0.0.0.0', port=port)



