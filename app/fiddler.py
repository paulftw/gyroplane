import logging
import string
from google.appengine.api import namespace_manager
from google.appengine.ext import ndb
from titan import files

key_alphabet = string.digits + string.lowercase
key_base = len(key_alphabet)


def namespaced(fn):
    from functools import wraps
    @wraps(fn)
    def wrapped(self, *args, **kwargs):
        old_namespace = namespace_manager.get_namespace()
        namespace_manager.set_namespace(self.get_sys_namespace())
        try:
            return fn(self, *args, **kwargs)
        finally:
            namespace_manager.set_namespace(old_namespace)
    return wrapped


class App(ndb.Model):

    @namespaced
    def write_file(self, name, data):
        logging.warn('\n\n****\n\nnwrite  %s  %s  ns=%s', self.get_file_obj(name), data, namespace_manager.get_namespace())
        return self.get_file_obj(name).write(data)

    @namespaced
    def read_file(self, name):
        return self.get_file_obj(name).read()

    def string_id(self):
        return id_to_string(self.key.id())

    @namespaced
    def get_file_obj(self, name):
        return files.File('/appcode_{}/{}'.format(self.string_id(), name))

    @namespaced
    def list_files(self):
        logging.warn('\n\n****\n\nread  %s  ns=%s', '/appcode_{}/'.format(self.string_id()), namespace_manager.get_namespace())
        return files.Files.list('/appcode_{}/'.format(self.string_id()))

    def get_sys_namespace(self):
        return ''
        return 'gyro_sys_' + self.string_id()



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


def save_app(files, subdomain=None):
    if subdomain is None:
        new_app = App()
        new_app.put()
    else:
        new_app = get_app(subdomain)
    for filename, data in files.items():
        new_app.write_file(filename, data)
    return True, new_app.string_id()


def get_code(subdomain):
    app = get_app(subdomain)
    file_list = app.list_files()

    files = [(filename, file.read()) for filename, file in file_list.items()]
    return files


def get_app(subdomain):
    if subdomain == 'null':
        return None
    return App.get_by_id(string_to_id(subdomain))


instances = {}

def load_app(subdomain, namespace):
    import flask
    app = flask.Flask(subdomain)
    app.config.update(DEBUG=True)

    app_data = get_app(subdomain)

    if app_data is None:
        return app

    try:
        compiled = compile(app_data.read_file('main.py'), '%s.gyroplane.io/main.py' % subdomain, 'exec')
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
