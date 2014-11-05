__author__ = 'paul'

from google.appengine.ext import ndb
from flask.ext import security

def init_security(app):
    from secrets import COOKIE_KEY
    app.secret_key = COOKIE_KEY
    # create and register flask.Security extension
    security.Security(app, MySecDatastore())


class User(ndb.Model):
    username = ndb.StringProperty()
    email = ndb.StringProperty()
    password = ndb.StringProperty()
    active = ndb.BooleanProperty()
    roles = ndb.StringProperty(repeated=True)
    created_at = ndb.DateTimeProperty(auto_now_add=True)
    modified_at = ndb.DateTimeProperty(auto_now_add=True)

class Role(ndb.Model):
    name = ndb.StringProperty()
    description = ndb.StringProperty()

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

