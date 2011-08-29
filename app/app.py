from flask import Flask, render_template, url_for
import datetime
from gaesessions import SessionMiddleware
from etudes.profile import gaeprofiles
from etudes.profile import get_current_profile

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

app.add_url_rule('/favicon.ico',
                 redirect_to=url_for('static', filename='hellokitty.ico'))

@app.route("/")
def homepage():
    profile = get_current_profile()
    return render_template('index.html', 
                           debug = [
                                    "G'day, %s!" % (profile.get_first_name()),
                           ])
