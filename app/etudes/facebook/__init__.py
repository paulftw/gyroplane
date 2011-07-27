from flask import Blueprint, render_template, request, abort
import facebook
import secrets

fbconnect = Blueprint('fbconnect', __name__, template_folder='templates')

@fbconnect.route('/fbpage', methods=['GET'])
def fbpage():
    return render_template('fbpage.html', 
                           fb_appId=secrets.FB_APPID, 
                           fb_user=fb_user())

def fb_user():
    cookie = facebook.get_user_from_cookie(
        request.cookies, secrets.FB_APPID, secrets.FB_SECRET)
    if cookie:
        # Store a local instance of the user data so we don't need
        # a round-trip to Facebook on every request
        graph = facebook.GraphAPI(cookie["access_token"])
        profile = graph.get_object("me")
        user = dict(id=str(profile["id"]),
                    name=profile["name"],
                    profile_url=profile["link"],
                    access_token=cookie["access_token"])
        return user
    return None
