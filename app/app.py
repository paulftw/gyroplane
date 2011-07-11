from flask import Flask, session, render_template

app = Flask(__name__)

import user

app.config.update(
    SECRET_KEY = 'g5498ug456ikt54',
    DEBUG = True
)

@app.route("/")
def hello():
    return render_template('index.html', session=dir(session))
