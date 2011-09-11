from flask import Blueprint, render_template, request
from etudes.profile import gaeprofiles, AuthMethod
import facebook
import secrets


fbprint = Blueprint('fbconnect', __name__, template_folder='templates')

@fbprint.route('/fbpage', methods=['GET'])
def fbpage():
    fbuser = fbconnector.auth_user
    return render_template('fbpage.html', 
                           cookies=request.cookies,
                           fb_appId=secrets.FB_APPID, 
                           fb_user=fbuser)


class FacebookConnect(AuthMethod):

    APPKEY = None
    APPSECRET = None

    def __init__(self, APPKEY, APPSECRET):
        self.APPKEY = APPKEY
        self.APPSECRET = APPSECRET

    def auth_user(self):
        """Returns the tuple (user_id, access_token), or None if user is 
        not signed in.
        """ 
        user_and_token = facebook.get_user_from_cookie(request.cookies, 
                self.APPKEY, self.APPSECRET)
        if user_and_token == None:
            return None
        return (user_and_token["uid"], user_and_token["access_token"])


    def get_profile_key(self):
        auth = self.auth_user
        if auth != None:
            return "fb!" + auth[0]
        else:
            return None
    
    def populate_profile(self, profile):
        auth = self.auth_user
        graph = facebook.GraphAPI(auth[1])
        me = graph.get_object("me")
        profile.first_name = me["first_name"]
        profile.name = me["name"]


fbconnector = FacebookConnect(secrets.FB_APPID, secrets.FB_SECRET)
