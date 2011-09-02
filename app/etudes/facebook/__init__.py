from flask import Blueprint, render_template, request
from etudes.profile import gaeprofiles
import facebook
import secrets

fbconnect = Blueprint('fbconnect', __name__, template_folder='templates')

@fbconnect.route('/fbpage', methods=['GET'])
def fbpage():
    cookies = request.cookies
    token = get_access_token(get_api_cookie(cookies))
    fbuser = get_user(token)
    if fbuser != None:
        populate_profile(fbuser, token)
    return render_template('fbpage.html', 
                           cookies=cookies,
                           fb_appId=secrets.FB_APPID, 
                           fb_user=fbuser)


def get_api_cookie(request_cookies):
    return facebook.get_user_from_cookie(
        request_cookies, secrets.FB_APPID, secrets.FB_SECRET)


def get_access_token(cookie):
    if cookie:
        return cookie["access_token"]
    else:
        return None


def get_user(access_token):
    if access_token:
        graph = facebook.GraphAPI(access_token)
        profile = graph.get_object("me")
        return profile
    return None


def populate_profile(fbuser, access_token):
    profile = gaeprofiles.current_profile
    
    profile.fb_id = fbuser["id"]
    profile.fb_token = access_token
    
    profile.first_name = fbuser["first_name"]
    profile.last_name = fbuser["name"]

