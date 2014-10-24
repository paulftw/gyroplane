"""
app.py

App Engine entry point and the Flask App object.
"""

import sys
sys.path.insert(0, './libs')
sys.path.insert(0, './libs.zip')

from flask import Flask, jsonify, render_template, request, send_from_directory
from flask.ext import security
from flask.ext.security import Security
from google.appengine.api import namespace_manager
from google.appengine.ext import db
from threading import Lock
import logging
import os

import fiddler



# GAE WSGI requires this object to be named app. Configurable in app.yaml
app = Flask(__name__)
root_app = app

# Switch to debug mode if we run on a dev_sever
app.config.update(
    DEBUG=os.environ['SERVER_SOFTWARE'].startswith('Development'))

app.config['DEFAULT_PARSERS'] = [
    'flask.ext.api.parsers.JSONParser',
    'flask.ext.api.parsers.URLEncodedParser',
    'flask.ext.api.parsers.MultiPartParser'
]

ROOT_DOMAIN = 'lvh.me'
PORT = 8080

app.config.update(SERVER_NAME='%s:%s' % (ROOT_DOMAIN, PORT))

from secrets import COOKIE_KEY
app.secret_key = COOKIE_KEY


@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(root_app.root_path, 'static'),
                               'favicon.ico',
                               mimetype='image/vnd.microsoft.icon')


@app.route("/", subdomain='<subdomain>')
def homepage(subdomain):
    return 'whoops ' + subdomain

@app.route("/")
def root_home():
    return render_template('admin/index.html')

@app.route("/get_code")
def get_code():
    fiddle_id = request.values['fiddle_id']
    return jsonify(fiddler.get_code(fiddle_id))

@app.route("/v1/<fiddle_id>")
def edit_fiddle(fiddle_id):
    return render_template('admin/index.html', debug="Loaded ID " + fiddle_id)

@app.route('/save', methods=['POST'])
def save():
    main_py = request.values.get('main_py', '')
    logging.warn('req vals = %s %s', request.values, request.get_json())
    main_py = request.get_json()['main_py']
    status, fiddle_id = fiddler.save_app(main_py)
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
        subdomain = self.get_subdomain(environ['HTTP_HOST'])
        namespace = 'gyro_' + subdomain if subdomain else ''
        try:
            sub_app = self.get_application(subdomain, namespace)
            namespace_manager.set_namespace(namespace)
            logging.warn('sub_app = %s', sub_app)
            return sub_app(environ, start_response)
        finally:
            namespace_manager.set_namespace("")

root_app = app


dispatcher = SubdomainDispatcher(ROOT_DOMAIN, fiddler.load_app)
dispatcher.instances[''] = root_app

# Make dispatcher the server's entry point
app = dispatcher
