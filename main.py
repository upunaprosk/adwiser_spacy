from flask import Flask, Markup, request, render_template
from models import generate_text

app = Flask(__name__)


@app.route('/')
def index():
    if request.args:
        text_to_inspect = request.args['text_to_inspect']
        annotation, comments = generate_text(text_to_inspect)
        annotation = Markup(annotation)
        return render_template("result.html", annotation=annotation, comments=comments)
    return render_template("main.html")


if __name__ == '__main__':
    app.run(debug=True)
