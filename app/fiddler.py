import logging
import string
from google.appengine.api import namespace_manager
from google.appengine.ext import ndb

key_alphabet = string.digits + string.lowercase
key_base = len(key_alphabet)


class App(ndb.Model):
    main_py = ndb.StringProperty(default="")


def id_to_string(x):
    digits = []
    while x:
        digits.append(key_alphabet[x % key_base])
        x /= key_base
    digits.reverse()
    return ''.join(digits)


def string_to_id(s):
    ret = 0
    for c in s:
        ret = ret * key_base + key_alphabet.index(c)
    return ret


def save_app(main_py, subdomain=None):
    new_app = App(main_py=main_py)
    new_app.put()
    return True, id_to_string(new_app.key.id())

def get_code(subdomain):
    app = get_app(subdomain)
    return {
        "main.py": app.main_py
    }

def get_app(subdomain):
    if subdomain == 'null':
        return None
    return App.get_by_id(string_to_id(subdomain))


instances = {}

def load_app(subdomain, namespace):
    import flask
    app = flask.Flask(subdomain)
    app.config.update(DEBUG=True)

    data = get_app(subdomain)

    if data is None:
        return app

    try:
        compiled = compile(data.main_py, '%s.gyroplane.io/main.py' % subdomain, 'exec')
    except Exception as e:
        return app

    try:
        namespace_manager.set_namespace(namespace)
        exec compiled in {
            'app': app,
            'flask': flask,
        }
        return app
    finally:
        namespace_manager.set_namespace("")
    return app
