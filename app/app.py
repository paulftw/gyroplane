from flask import Flask, render_template, request
import datetime
from gaesessions import SessionMiddleware, get_current_session

from secrets import COOKIE_KEY
import etudes.users
from etudes.facebook import fbconnect

app = Flask(__name__)

# Enable gae-sessions
app.wsgi_app = SessionMiddleware(app.wsgi_app, cookie_key=COOKIE_KEY,
                                 lifetime=datetime.timedelta(days=31))

# Switch to debug mode
app.config.update(DEBUG = False)


# Register blueprints
app.register_blueprint(fbconnect)

@app.route("/")
def homepage():
    session = get_current_session()
    if session.has_key('counter'):
        session['counter'] += 1
    else:
        session['counter'] = 100
    return render_template('index.html', debug = [session['counter'], __name__])
