"""
    User profile
""" 

from google.appengine.ext import db

class Profile(db.Model):
    first_name = db.StringProperty()
    last_name = db.StringProperty()
    birth_date = db.DateProperty()
    last_login = db.DateTimeProperty()
    
    fb_id = db.StringProperty()
    twitter_id = db.StringProperty()
    goog_id = db.StringProperty()

