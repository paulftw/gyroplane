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

    domains = ndb.StringProperty(repeated=True)

    @namespaced
    def write_file(self, name, data):
        return self.get_file_obj(name).write(data)

    @namespaced
    def delete_file(self, name):
        return self.get_file_obj(name).delete()

    @namespaced
    def read_file(self, name):
        return self.get_file_obj(name).read()

    def string_id(self):
        return id_to_string(self.key.id())

    @namespaced
    def get_file_obj(self, name):
        if not name.startswith('/'):
            name = '/' + name
        return files.File(name)

    @namespaced
    def list_files(self):
        return files.Files.list('/')

    def get_sys_namespace(self):
        return 'gyro_sys_' + self.string_id()

    @classmethod
    def find_by_domain(cls, domain):
        return cls.query(cls.domains == domain).get()


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


def save_app(files, deleted_files={}, fiddle_id=None):
    if fiddle_id is None:
        new_app = App()
        new_app.put()
    else:
        new_app = get_app(fiddle_id)
    for filename, data in files.items():
        new_app.write_file(filename, data)

    for filename in deleted_files.keys():
        try:
            new_app.delete_file(filename)
        except:
            # Ignore non-existing file
            pass
    return True, new_app.string_id()


def get_files(subdomain):
    app = get_app(subdomain)
    file_list = app.list_files()

    files = dict([(filename[1:], app.read_file(filename)) for filename, file in file_list.items()])
    return files


def get_app(fiddle_id):
    if fiddle_id == 'null':
        return None
    res = None
    try:
        res = App.find_by_domain(fiddle_id)
    except:
        logging.exception('Hit for unknown domain %s', fiddle_id)
    if res is not None:
        return res
    return App.get_by_id(string_to_id(fiddle_id))


instances = {}

def load_app(subdomain, namespace):
    import flask

    app_pkg = 'gyro_app_' + ''.join([x if x in key_alphabet else '_' for x in subdomain.lower()])
    app = flask.Flask(app_pkg)
    app.config.update(DEBUG=True)

    app_data = get_app(subdomain)

    if app_data is None:
        return app

    def tpl_loader(name):
        return app_data.read_file(name)
    from jinja2 import FunctionLoader
    app.jinja_loader = FunctionLoader(tpl_loader)

    try:
        compiled = compile(app_data.read_file('main.py'), '%s.gyroplane.io/main.py' % subdomain, 'exec')
    except Exception as e:
        logging.exception('Compilation failed for %s', app)
        return app

    try:
        namespace_manager.set_namespace(namespace)
        exec compiled in {
            'app': app,
        }
        return app
    finally:
        namespace_manager.set_namespace("")
    return app
