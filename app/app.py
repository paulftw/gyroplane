from flask import Flask, render_template, send_from_directory
import datetime
import os
import logging
from etudes.profile import gaeprofiles, decorate_wsgi_app
import gaesessions

from secrets import COOKIE_KEY

app = Flask(__name__)

# Enable gae-sessions
app.wsgi_app = decorate_wsgi_app(app.wsgi_app, cookie_key=COOKIE_KEY,
                                 lifetime=datetime.timedelta(days=31))

# Switch to debug mode
app.config.update(DEBUG = True)


# Register blueprints
app.register_blueprint(gaeprofiles)


@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'),
                               'hellokitty.ico', 
                               mimetype='image/vnd.microsoft.icon')


@app.route("/")
def homepage():
    profile = gaesessions.get_current_session().profile
    return render_template('index.html', 
                           debug = [
                                    profile.__dict__,
                           ])
