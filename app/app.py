"""
app.py

App Engine entry point and the Flask App object.
"""

import sys
sys.path.insert(0, './libs')
sys.path.insert(0, './libs.zip')

#import dropbox
from flask import Flask, jsonify, render_template, request, send_from_directory
from google.appengine.api import namespace_manager
from threading import Lock
import logging
import os
import re
from titan import users

#dropbox_app_key = 'ledpbimuh7smq2g'
#dropbox_app_secret = 'g6z2t8ojqrodlup'

#flow = dropbox.client.DropboxOAuth2FlowNoRedirect(app_key, app_secret)


import fiddler


DEFAULT_FILES = {
    'main.py':
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

""",
    'main.html':
"""<h1>Hello World!</h1>
<p>
    Try <a href=/counter>counter</a>
</p>
""",
    'counter.html':
"""<p>This page has been visited {{ counter }} time(s)</p>
<a href=/counter>Refresh</a>
""",
    'static/css/style.css':
"""html {
    background-color: #eee;
}"""
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

#from security import init_security
#init_security(app)


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
            files = {'main.py': 'DO NOT SAVE!!!\nNot Authorized to view code. '}
            domains = ['example.com']

    return render_template('admin/index.html', context=dict(
        SERVER_NAME=SERVER_NAME,
        files=files,
        domains=domains,
        authorized=authorized,
        login_url=login_url,
        fiddle_id=fiddle_id,
    ))


@app.route('/save', methods=['POST'])
def save():
    user = users.get_current_user()
    if user is None or not user.is_admin:
        return jsonify(status="Not Authorized")

    request_json = request.get_json()
    fiddle_id = request_json.get('fiddle_id', None)
    files = request_json['files']
    deleted_files = request_json.get('deleted_files', {})
    status, fiddle_id = fiddler.save_app(files, deleted_files, fiddle_id=fiddle_id)
    dispatcher.unload_app(fiddle_id)
    return jsonify(status=status, fiddle_id=fiddle_id)

#from flask.ext.validate import type
#from flask.ext import validate


#schema=validate.schema()

@app.route('/save_domains', methods=['POST'])
#@validate.flask_json(fiddle_id=lid.string(required=True),
#                     domains=type.array(lid.string(max_length=100), min_length=1, max_length=10))
#@validate.expand_args()
def save_domains(fiddle_id, domains):
    request_json = request.get_json()
    fiddle_id = request_json.get('fiddle_id', None)
    domains = request_json['domains']
    fiddler.set_domains(fiddle_id, domains)



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

    def get_application(self, subdomain, namespace):
        with self.lock:
            app = self.instances.get(subdomain)
            if app is None:
                app = self.create_app(subdomain, namespace)
                self.instances[subdomain] = app
            return app

    def __call__(self, environ, start_response):
        namespace_manager.set_namespace("")
        app_domain = self.get_subdomain(environ['HTTP_HOST'])
        if app_domain == 'www':
            app_domain = ''
        if app_domain in ['', 'www']:
            namespace = ''
        else:
            namespace = 'gyro_' + app_domain.replace('.', '_').replace('-', '_').replace(':', '_')
        try:
            sub_app = self.get_application(app_domain, namespace)
            if hasattr(sub_app, 'get_sys_namespace'):
                namespace_manager.set_namespace(sub_app.get_sys_namespace())
            return sub_app(environ, start_response)
        finally:
            namespace_manager.set_namespace("")

    def insert_app(self, domain, app):
        with self.lock:
            self.instances[domain] = app

    def unload_app(self, domain):
        with self.lock:
            inst = self.instances.pop(domain, None)
            if inst is None:
                return
            key = id(inst)
            for k, v in self.instances.items():
                if id(v) == key:
                    self.instances.pop(k, None)


root_app = app

dispatcher = SubdomainDispatcher(ROOT_DOMAIN, fiddler.load_app)
dispatcher.insert_app('', root_app)
dispatcher.insert_app(ROOT_DOMAIN, root_app)

# Make dispatcher the server's entry point
app = dispatcher
