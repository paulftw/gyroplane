from flask import Flask, render_template, send_from_directory
import datetime
import os
import logging
from gaesessions import SessionMiddleware
from etudes.profile import gaeprofiles

from secrets import COOKIE_KEY
from etudes.facebook import fbconnect

app = Flask(__name__)

# Enable gae-sessions
app.wsgi_app = SessionMiddleware(app.wsgi_app, cookie_key=COOKIE_KEY,
                                 lifetime=datetime.timedelta(days=31))

# Switch to debug mode
app.config.update(DEBUG = True)


# Register blueprints
app.register_blueprint(fbconnect)
app.register_blueprint(gaeprofiles)


@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'),
                               'hellokitty.ico', 
                               mimetype='image/vnd.microsoft.icon')


@app.route("/")
def homepage():
    profile = gaeprofiles.current_profile
    return render_template('index.html', 
                           debug = [
                                    "first name: %s!" % (profile.get_first_name()),
                           ])
