import base64
import logging
import string
from google.appengine.api import namespace_manager
from google.appengine.ext import ndb
from titan import files
from werkzeug.exceptions import NotFound

key_alphabet = string.digits + string.lowercase
key_base = len(key_alphabet)

DEFAULT_APP_ID = 'defaultapp'

def touch_default_app(files, server_name):
    default_app = App.get_by_id(DEFAULT_APP_ID)
    if default_app is None:
        default_app = App.get_or_insert(DEFAULT_APP_ID)
        for f, data in files.items():
            default_app.write_file(f, data)

    def_domain = DEFAULT_APP_ID + '.' + server_name
    if def_domain not in default_app.domains:
        default_app.domains.append(def_domain)
        default_app.put()




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
            pass
    return wrapped


class App(ndb.Model):

    domains = ndb.StringProperty(repeated=True)
    fiddle_id = ndb.StringProperty()

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
        key_id = self.key.id()
        if isinstance(key_id, basestring):
            return key_id
        else:
            return id_to_string(key_id)

    @namespaced
    def get_file_obj(self, name):
        if not name.startswith('/'):
            name = '/' + name
        return files.File(name, namespace=namespace_manager.get_namespace())

    @namespaced
    def list_files(self):
        return files.Files.list('/', recursive=True)

    def get_sys_namespace(self):
        return 'gyro_' + self.string_id()

    @classmethod
    def find_by_domain(cls, domain):
        logging.info('App DB Lookup for domain %s', domain)
        res = cls.query(cls.domains == domain).get()
        logging.info('Loaded app %s %s', res, res.key if res is not None else res)
        return res


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
    if 'main.py' in deleted_files:
        del deleted_files['main.py']
    if fiddle_id is None:
        new_app = App()
        new_app.put()
        if 'main.py' not in files:
            files['main.py'] = ''
    else:
        new_app = get_app(fiddle_id)

    if new_app.fiddle_id is None:
        new_app.fiddle_id = new_app.string_id()
        new_app.put()

    for filename in deleted_files.keys():
        try:
            new_app.delete_file(filename)
        except:
            # Ignore non-existing file
            pass

    for filename, data in files.items():
        if isinstance(data, dict):
            assert data['is_binary']
            if data.get('is_lazy', False):
                continue
            data = base64.b64decode(data['data'])
        new_app.write_file(filename, data)

    return True, new_app.string_id()


def save_domains(fiddle_id, domains):
    if fiddle_id is None:
        raise error #TODO
    app = get_app(fiddle_id)
    if app is None:
        raise error #TODO
    app.domains = domains
    app.put()


def get_files_and_domains(subdomain):
    app = get_app(subdomain)
    file_list = app.list_files()

    def get_file_content(filename):
        content = app.read_file(filename)
        try:
            return unicode(content)
        except UnicodeDecodeError:
            res = {
                'is_binary': True,
                'data': base64.standard_b64encode(content),
            }
            if len(res['data']) > 32 * 1024:
                res['data'] = ''
                res['is_lazy'] = True
            return res

    files = dict([(filename[1:], get_file_content(filename)) for filename, file in file_list.items()])
    return files, app.domains


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
    try:
        return App.get_by_id(string_to_id(fiddle_id))
    except ValueError:
        # string_by_id raises ValueError when string isn't a fiddle id.
        return None



instances = {}

def load_app(subdomain):
    import flask

    app_pkg = 'gyro_app_' + ''.join([x if x in key_alphabet else '_' for x in subdomain.lower()])
    app = flask.Flask(app_pkg, static_folder=None)
    app.config.update(DEBUG=True)

    import os
    if os.environ.get('SERVER_SOFTWARE', '').startswith('Development'):
        app.config.update(SEND_FILE_MAX_AGE_DEFAULT=10)
    else:
        app.config.update(SEND_FILE_MAX_AGE_DEFAULT=3600)

    app_data = get_app(subdomain)

    if app_data is None:
        return app, True, None

    def tpl_loader(name):
        return app_data.read_file(name)
    from jinja2 import FunctionLoader
    app.jinja_loader = FunctionLoader(tpl_loader)


    def override_send_file(filename):
        filename = '/static/' + filename
        cache_timeout = app.get_send_file_max_age(filename)
        file = app_data.get_file_obj(filename)
        if not file.exists:
            raise NotFound()

        class FileReadOnce(object):
            def __init__(self):
                self.already_read = False

            def read(self, buf_size=0):
                if self.already_read:
                    return None
                self.already_read = True
                content = app_data.read_file(filename)
                if isinstance(content, unicode):
                    content = content.encode('utf-8')
                return content

        file = FileReadOnce()

        from flask.helpers import send_file
        return send_file(file, attachment_filename=filename, cache_timeout=cache_timeout, conditional=True)

    app.send_static_file = override_send_file
    app.static_folder = '/static'
    app.add_url_rule('/static' + '/<path:filename>',
                              endpoint='static',
                              view_func=app.send_static_file)

    try:
        compiled = compile(app_data.read_file('main.py'), '%s.gyroplane.io/main.py' % subdomain, 'exec')
    except Exception as e:
        logging.exception('Compilation failed for %s', app)
        return app

    try:
        namespace_manager.set_namespace(app_data.get_sys_namespace())
        exec compiled in {
            'app': app,
        }
        return app, False, app_data.get_sys_namespace()
    finally:
        namespace_manager.set_namespace("")
    return app, True, None
