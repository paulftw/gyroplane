from flask import Flask, session, render_template

app = Flask(__name__)

import fbsdk

from secrets import configure_secrets
configure_secrets(app)

app.config.update(
    DEBUG = True,
)

app.config.update(


@app.route("/")
def hello():
    return render_template('index.html', debug=dir(session))
