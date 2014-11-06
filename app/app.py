"""
app.py

App Engine entry point and the Flask App object.
"""

import sys
sys.path.insert(0, './libs')
sys.path.insert(0, './libs.zip')

from flask import Flask, jsonify, render_template, request, send_from_directory
from google.appengine.api import namespace_manager
from threading import Lock
import logging
import os

import fiddler



# GAE WSGI requires this object to be named app. Configurable in app.yaml
app = Flask(__name__)
root_app = app

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


#from security import init_security
#init_security(app)


@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(root_app.root_path, 'static'),
                               'favicon.ico',
                               mimetype='image/vnd.microsoft.icon')


@app.route("/")
def root_home():
    return render_template('admin/index.html', context=dict(
        SERVER_NAME=SERVER_NAME,
    ))


@app.route("/v0/<fiddle_id>")
def edit_fiddle(fiddle_id):
    files = fiddler.get_files(fiddle_id)
    return render_template('admin/index.html', context=dict(
        SERVER_NAME=SERVER_NAME,
        files=files,
        fiddle_id=fiddle_id,
    ))


@app.route('/save', methods=['POST'])
def save():
    request_json = request.get_json()
    fiddle_id = request_json.get('fiddle_id', None)
    files = request_json['files']
    deleted_files = request_json.get('deleted_files', {})
    status, fiddle_id = fiddler.save_app(files, deleted_files, fiddle_id=fiddle_id)
    return jsonify(status=status, fiddle_id=fiddle_id)


class SubdomainDispatcher(object):

    def __init__(self, domain, create_app):
        self.domain = domain
        self.create_app = create_app
        self.lock = Lock()
        self.instances = {}

    def get_subdomain(self, host):
        host = host.split(':')[0]
        assert host.endswith(self.domain),\
            'Configuration error host: %s, self.domain: %s' % (host, self.domain)
        host = host[:-len(self.domain)]
        return host.rstrip('.')

    def get_application(self, subdomain, namespace):
        with self.lock:
            app = self.instances.get(subdomain)
            if app is None:
                logging.info('Loading app for subdomain %s', subdomain)
                app = self.create_app(subdomain, namespace)
                self.instances[subdomain] = app
            return app

    def __call__(self, environ, start_response):
        namespace_manager.set_namespace("")
        subdomain = self.get_subdomain(environ['HTTP_HOST'])
        if subdomain == 'www':
            subdomain = ''
        namespace = 'gyro_' + subdomain if subdomain else ''
        try:
            sub_app = self.get_application(subdomain, namespace)
            namespace_manager.set_namespace(namespace)
            return sub_app(environ, start_response)
        finally:
            namespace_manager.set_namespace("")


root_app = app

dispatcher = SubdomainDispatcher(ROOT_DOMAIN, fiddler.load_app)
dispatcher.instances[''] = root_app

# Make dispatcher the server's entry point
app = dispatcher
