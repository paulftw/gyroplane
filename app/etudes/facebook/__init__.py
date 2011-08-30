from flask import Blueprint, render_template
from etudes.profile import get_current_profile
import facebook
import secrets

fbconnect = Blueprint('fbconnect', __name__, template_folder='templates')

@fbconnect.route('/fbpage', methods=['GET'])
def fbpage():
    fbuser = get_user(get_access_token(get_api_cookie()))
    if fbuser != None:
        populate_profile()
    return render_template('fbpage.html', 
                           cookies=request.cookies,
                           fb_appId=secrets.FB_APPID, 
                           fb_user=fb_user())


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
        # Store a local instance of the user data so we don't need
        # a round-trip to Facebook on every request
        graph = facebook.GraphAPI()
        profile = graph.get_object("me")
        user = dict(id=str(profile["id"]),
                    name=profile["name"],
                    profile_url=profile["link"],
                    access_token=cookie["access_token"])
        return user
    return None


def populate_profile(access_token):
    user = get_user(access_token)
    profile = get_current_profile()
    
    profile.fb_id = user["id"]
    profile.fb_token = access_token
    
    profile.first_name = user["first_name"]
    profile.last_name = user["name"]

