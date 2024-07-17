import flask

app = flask.Flask(__name__)

@app.route('/v1/chat/completions')
def hi():
    return "Hi"
