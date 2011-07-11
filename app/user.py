# User accounts, OpenID, etc.

from app import app

from flask import g, session, request, render_template, flash, redirect
from flaskext.openid import OpenID

from google.appengine.ext import db
from openid_store import DatastoreStore


oid = OpenID(app, store_factory=DatastoreStore)


@app.route('/login', methods=['GET', 'POST'])
@oid.loginhandler
def login():
    if g.user is not None:
        return redirect(oid.get_next_url())
    if request.method == 'POST':
        openid = request.form.get('openid')
        if openid:
            return oid.try_login(openid, ask_for=['email', 'fullname',
                                                  'nickname'])
    return render_template('login.html', next=oid.get_next_url(),
        error=oid.fetch_error())
    
                           
@oid.after_login
def create_or_login(resp):
    session['openid'] = resp.identity_url
    flash(u'Successfully signed in id=%s, name=%s, nick=%s, email=%s' 
        % (resp.identity_url, resp.fullname, resp.nickname, resp.email))
    return redirect(oid.get_next_url())


@app.before_request
def before_request():
    g.user = None
    if 'openid' in session:
        oid = session['openid']
        q = db.Query(User)
        q.filter('openid =', oid)
        #g.user = q.fetch(1)[0]
        g.user = oid
        print 'for openid', oid, 'found user', g.user


@app.route('/logout')
def logout():
    session.pop('openid', None)
    flash(u'You were signed out')
    return redirect(oid.get_next_url())


class User(db.Model):
    name = db.StringProperty(required = True)
    created = db.DateTimeProperty(auto_now_add = True)
    email = db.StringProperty(required = True)
    openid = db.StringProperty(required = True)

def __init__():
    print "Started users module"
    pass
