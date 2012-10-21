from flask import Flask, render_template, request, send_from_directory
import datetime
import os
import logging
#from etudes.profile import decorate_app
#import gaesessions

from secrets import COOKIE_KEY
app = Flask(__name__)
app.secret_key = COOKIE_KEY

# Enable gae-sessions
#app.wsgi_app = decorate_app(app.wsgi_app, cookie_key=COOKIE_KEY,
#                                 lifetime=datetime.timedelta(days=31))

from flask.ext.security import User, Security, login_required, roles_accepted, datastore, login_user

from google.appengine.ext import db
class User(db.Model):
    username = db.StringProperty()
    email = db.StringProperty()
    password = db.StringProperty()
    active = db.BooleanProperty()
    roles = db.StringListProperty()
    created_at = db.DateTimeProperty(auto_now_add=True)
    modified_at = db.DateTimeProperty(auto_now_add=True)

class Role(db.Model):
    name = db.StringProperty()
    description = db.StringProperty()

class MySec(datastore.UserDatastore):
    def __init__(self):
        pass

    def get_models(self):
        return (User, Role)

    def _save_model(self, model):
        model.put()

    def _do_with_id(self, id):
        return User.get_by_id(id)

    def _do_find_user(self, user):
        by_email = User.gql("where email = :1", user).get()
        if by_email is None:
            return User.gql("where username = :1", user).get()

    def _do_find_role(self, role):
        return Role.gql("where name = :1", role).get()


Security(app, MySec())


# Switch to debug mode
app.config.update(
    DEBUG = os.environ['SERVER_SOFTWARE'].startswith('Development'))


@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'),
                               'hellokitty.ico', 
                               mimetype='image/vnd.microsoft.icon')


@app.route("/")
def homepage():
    return "this is homepage"
    return render_template('index.html', 
                           debug = [
                                    (),
                           ])

@app.route("/login", methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        next = request.values.get('next', '/')
        return render_template('login.html',
                               next=request.environ.keys())
    elif request.method == 'POST':
        u = User(email=request.values.get('email'))
        login_user(u)


@app.route("/secret")
@login_required
def secret():
    return "login form"
