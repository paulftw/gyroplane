"""
app.py

App Engine entry point and the Flask App object.
"""

import sys
sys.path.insert(0, './libs')
sys.path.insert(0, './libs.zip')

from flask import Flask, jsonify, render_template, redirect, request, send_file, send_from_directory, session, url_for
from google.appengine.api import namespace_manager
from threading import Lock
import logging
import os
import re
from titan import users

import fiddler


DEFAULT_FILES = {
    'main.py': { 'content':
"""from flask import render_template

@app.route('/')
def homepage():
    return render_template('main.html')


view_count = 0

@app.route('/counter')
def counter():
    global view_count
    view_count = view_count + 1
    return render_template('counter.html', counter=view_count)

"""},

    'main.html': { 'content':
"""<h1>Hello World!</h1>
<p>
    Try <a href=/counter>counter</a>
</p>
"""},

    'counter.html': { 'content':
"""<p>This page has been visited {{ counter }} time(s)</p>
<a href=/counter>Refresh</a>
""",
    'static/css/style.css':
"""html {
    background-color: #eee;
}"""},
}


# GAE WSGI requires this object to be named app. Configurable in app.yaml
app = Flask(__name__)
root_app = app

root_app.jinja_options = root_app.jinja_options.copy()
root_app.jinja_options.update(dict(
        block_start_string='<%',
        block_end_string='%>',
        variable_start_string='{%',
        variable_end_string='%}',
        comment_start_string='<#',
        comment_end_string='#>',
    ))

# Switch to debug mode if we run on a dev_server
DEBUG_MODE = os.environ.get('SERVER_SOFTWARE', '').startswith('Development')
app.config.update(DEBUG=DEBUG_MODE)

app.config['DEFAULT_PARSERS'] = [
    'flask.ext.api.parsers.JSONParser',
    'flask.ext.api.parsers.URLEncodedParser',
    'flask.ext.api.parsers.MultiPartParser'
]

from secrets import FLASK_SECRET_KEY
app.config['SECRET_KEY'] = FLASK_SECRET_KEY

SERVER_NAME = None

if DEBUG_MODE:
    ROOT_DOMAIN = 'lvh.me'
    #ROOT_DOMAIN = 'localhost'
    PORT = 8080
    SERVER_NAME = '%s:%s' % (ROOT_DOMAIN, PORT)
else:
    ROOT_DOMAIN = 'gyroplane.io'
    PORT = 80
    SERVER_NAME = '%s' % (ROOT_DOMAIN, )


fiddler.touch_default_app(DEFAULT_FILES, SERVER_NAME)


@app.route("/dbox_start/<fiddle_id>")
def dbox_start(fiddle_id):
    from dboxsync import get_dropbox_client, get_dropbox_flow
    if get_dropbox_client() is None:
        return redirect(get_dropbox_flow().start(fiddle_id))
    else:
        return redirect(url_for('root_home', fiddle_id=fiddle_id))

@app.route("/dbo2")
def dboxo2():
    from dboxsync import get_dropbox_flow
    access_token, user_id, url_state = get_dropbox_flow().finish(request.args)
    session['dbox-token'] = access_token
    session['dbox-user-id'] = user_id
    return redirect("/v0/" + url_state)


@app.route('/sync_dbxo', methods=['POST'])
def sync_dbox():
    user = users.get_current_user()
    if user is None or not user.is_admin:
        return jsonify(status="Not Authorized")

    request_json = request.get_json()
    fiddle_id = request_json.get('fiddle_id', None)

    user = users.get_current_user()
    authorized = user is not None and user.is_admin
    if not authorized:
        return "NotAuthorized"

    files, domains = fiddler.get_files_and_domains(fiddle_id, include_blobs=True)

    if (request_json.get('load_from_dbox') is not None) and (request_json.get('write_to_dbox') is None):
        from dboxsync import load_from_dbox
        return jsonify(loaded_from_dbox=load_from_dbox(fiddle_id, files))

    if (request_json.get('load_from_dbox') is None) and (request_json.get('write_to_dbox') is not None):
        status, fiddle_id = _do_save(files, {}, fiddle_id=fiddle_id)
        return jsonify(written_to_dbox=status)


@app.route('/get_dbox_state', methods=['POST'])
def get_dbox():
    user = users.get_current_user()
    if user is None or not user.is_admin:
        return jsonify(status="Not Authorized")

    request_json = request.get_json()
    fiddle_id = request_json.get('fiddle_id', None)

    files, domains = fiddler.get_files_and_domains(fiddle_id, include_blobs=True)

    from dboxsync import get_sync_state
    return jsonify(get_sync_state(fiddle_id, files))

@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(root_app.root_path, 'static'),
                               'favicon.ico',
                               mimetype='image/vnd.microsoft.icon')


@app.route("/")
@app.route("/v0/<fiddle_id>")
def root_home(fiddle_id=None):
    user = users.get_current_user()
    authorized = user is not None and user.is_admin

    domains = []
    files = DEFAULT_FILES

    if not authorized:
        login_url = users.create_login_url('/v0/' + fiddle_id if fiddle_id else '/')
    else:
        login_url = ''

    if fiddle_id is not None:
        if authorized:
            files, domains = fiddler.get_files_and_domains(fiddle_id)
        else:
            files = {'main.py': {'content': 'DO NOT SAVE!!!\nNot Authorized to view code. '}}
            domains = ['example.com']

    from dboxsync import get_sync_state, get_dropbox_client

    return render_template('admin/index.html', context=dict(
        SERVER_NAME=SERVER_NAME,
        files=files,
        domains=domains,
        authorized=authorized,
        login_url=login_url,
        fiddle_id=fiddle_id,
        sync_state=get_sync_state(fiddle_id, files),
        dropbox_connected=get_dropbox_client() is not None
    ))


@app.route("/v0/download/<fiddle_id>")
def download_fiddle(fiddle_id):
    user = users.get_current_user()
    authorized = user is not None and user.is_admin

    if not authorized:
        return 'Downloaded. Not.'

    files, domains = fiddler.get_files_and_domains(fiddle_id, include_blobs=True)
    import bulker, datetime
    now = datetime.datetime.now().strftime('%Y.%m.%d')
    zip_content = bulker.generate_zip(files)
    return send_file(zip_content,
                     mimetype='application/octet-stream',
                     as_attachment=True,
                     attachment_filename='%s.%s.zip' % (fiddle_id, now))


@app.route('/save', methods=['POST'])
def save():
    user = users.get_current_user()
    if user is None or not user.is_admin:
        return jsonify(status="Not Authorized")

    request_json = request.get_json()
    fiddle_id = request_json.get('fiddle_id', None)
    files = request_json['files']
    deleted_files = request_json.get('deleted_files', {})

    status, fiddle_id = _do_save(files, deleted_files, fiddle_id)
    return jsonify(status=status, fiddle_id=fiddle_id)

def _do_save(files, deleted_files, fiddle_id):
    from dboxsync import get_dropbox_client
    status, fiddle_id = fiddler.save_app(files, deleted_files, fiddle_id=fiddle_id, dbox_client=get_dropbox_client())
    dispatcher.unload_app(fiddle_id)
    return (status, fiddle_id)

#from flask.ext.validate import type
#from flask.ext import validate


#schema=validate.schema()

@app.route('/save_domains', methods=['POST'])
#@validate.flask_json(fiddle_id=lid.string(required=True),
#                     domains=type.array(lid.string(max_length=100), min_length=1, max_length=10))
#@validate.expand_args()
def save_domains():
    request_json = request.get_json()
    fiddle_id = request_json.get('fiddle_id', None)
    domains = request_json['domains']
    fiddler.save_domains(fiddle_id, domains)
    return 'OK'



class SubdomainDispatcher(object):

    def __init__(self, domain, create_app):
        self.domain = domain
        self.create_app = create_app
        self.lock = Lock()
        self.instances = {}

    def get_subdomain(self, host):
        host = host.lower().split(':')[0]
        if not host.endswith(self.domain):
            # Used to be: 'Configuration error host: %s, self.domain: %s' % (host, self.domain)
            return host

        host = host[:-len(self.domain)]
        app_domain = host.rstrip('.')
        if app_domain == 'www':
            return ''
        return app_domain

    def get_application(self, subdomain, url):
        if url.startswith('/_titan/'):
            return None, None
            from titan.files.handlers import application
            application.get_sys_namespace = lambda: subdomain
            return application
        if url.startswith('/echoecho/'):
            return echo, None

        with self.lock:
            app, namespace = self.instances.get(subdomain, (None, None))
            if app is None:
                app, is_default, namespace = self.create_app(subdomain)
                if not is_default:
                    self.instances[subdomain] = (app, namespace)
            return app, namespace

    def __call__(self, environ, start_response):
        namespace_manager.set_namespace("")
        app_domain = self.get_subdomain(environ['HTTP_HOST'])
        if app_domain == 'www':
            app_domain = ''
        try:
            sub_app, namespace = self.get_application(app_domain, url=environ['PATH_INFO'])
            if namespace is not None:
                namespace_manager.set_namespace(namespace)
            return sub_app(environ, start_response)
        finally:
            namespace_manager.set_namespace("")

    def insert_app(self, domain, app, namespace=None):
        with self.lock:
            self.instances[domain] = (app, namespace)

    def unload_app(self, fiddle_id):
        with self.lock:
            for k, v in self.instances.items():
                if v[1] is not None and v[1].endswith(fiddle_id):
                    self.instances.pop(k, None)


root_app = app

dispatcher = SubdomainDispatcher(ROOT_DOMAIN, fiddler.load_app)
dispatcher.insert_app('', root_app)
dispatcher.insert_app(ROOT_DOMAIN, root_app)
dispatcher.insert_app('3-alpha-dot-gyroplaneio.appspot.com', root_app)

# Make dispatcher the server's entry point
app = dispatcher


def echo(environ, start_response):
    status = '200 OK'
    response_headers = [('Content-type', 'text/plain')]
    start_response(status, response_headers)
    return map(lambda x: str(x) + '\n', environ.items())