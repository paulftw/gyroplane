"""
app.py

App Engine entry point and the Flask App object.
"""

import sys
sys.path.insert(0, './libs')
sys.path.insert(0, './libs.zip')

from flask import Flask, render_template, request, send_from_directory
from flask.ext import security
from flask.ext.security import Security
from google.appengine.ext import db
import os
import logging



# GAE WSGI requires this object to be named app. Configurable in app.yaml
app = Flask(__name__)

# Switch to debug mode if we run on a dev_sever
app.config.update(
    DEBUG = os.environ['SERVER_SOFTWARE'].startswith('Development'))

from secrets import COOKIE_KEY
app.secret_key = COOKIE_KEY


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

class MySecDatastore(security.datastore.UserDatastore):
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

# create and register flask.Security extension
Security(app, MySecDatastore())


@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'),
                               'hellokitty.ico', 
                               mimetype='image/vnd.microsoft.icon')


@app.route("/")
def homepage():
    return render_template('index.html', 
                           debug = [
                                    'info',
                           ])


@app.route("/login", methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        next = request.values.get('next', '/')
        return render_template('security/login.html',
                               next=next)
    elif request.method == 'POST':
        u = User(email=request.values.get('email'))
        security.login_user(u)


@app.route("/secret")
@security.login_required
def secret():
    return "secret page for logged in users"
