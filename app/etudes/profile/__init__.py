"""
    User profile
""" 

from flask import Blueprint, request
import gaesessions
from google.appengine.ext import db
from datetime import datetime, timedelta

gaeprofiles = Blueprint('gaeprofiles', __name__)

@gaeprofiles.after_request
def persist_profile():
    get_current_profile().save()

PROFILE_KEY = 'PK_profile_id'

UPDATE_INTERVAL = timedelta(minutes=10)

class Profile(db.Expando):
    first_name = db.StringProperty()
    name = db.StringProperty()
    last_login_time = db.DateTimeProperty()

    fb_id = db.StringProperty()
    fb_token = db.StringProperty()
    
    twitter_id = db.StringProperty()
    goog_id = db.StringProperty()
    
    dirty = False
    
    def get_first_name(self):
        if self.first_name != None:
            return self.first_name
        else:
            return self.name
    
    def save(self):
        if not self.dirty and self.is_too_old():
            self.dirty = True
            self.last_login_time = datetime.utcnow()
        if self.dirty:
            self.put()
            self.dirty = False
    
    def is_too_old(self):
        if self.last_login_time == None:
            return True
        delta = datetime.utcnow() - self.last_login_time
        return delta > UPDATE_INTERVAL
    
    def get_id(self):
        return self.key().id_or_name()
    
    def debug_dump(self):
        return 'Profile summary: id %s, fn %s; ln %s; bd %s; ll %s;' % \
            (self.get_id(),
             self.first_name, 
             self.name, 
             self.birth_date, 
             self.last_login_time,
            )


def create_profile():
    profile = Profile()
    profile.put()
    profile.name = 'Guest' + str(profile.get_id())
    profile.dirty = True
    return profile


def get_current_profile():
    session = gaesessions.get_current_session()
    profile = None
    if session.has_key(PROFILE_KEY):
        profile = load_or_create(session[PROFILE_KEY])
    else:
        profile = create_profile()
    session[PROFILE_KEY] = profile.get_id()
    return profile


def load_or_create(profile_id):
    profile = None
    if profile_id == None:
        profile = create_profile()
    else:
        profile = Profile.get_by_id(profile_id)
        if profile == None:
            profile = create_profile()
    return profile    

