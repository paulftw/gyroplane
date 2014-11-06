__author__ = 'paul'

from app import fiddler
import unittest
from nose.tools import eq_
from google.appengine.ext import testbed

class FiddlerTestCase(unittest.TestCase):

    def setUp(self):
        # Setup AppEngine testbed
        self.testbed = testbed.Testbed()
        self.testbed.activate()
        self.testbed.init_datastore_v3_stub()
        self.testbed.init_memcache_stub()

    def test_create_load(self):
        status, subdomain = fiddler.save_app({'foo.py': 'bar baz'}, {})
        files = fiddler.get_files(subdomain)
        eq_(files, dict([('foo.py', 'bar baz')]))

        # overwrite
        status2, subdomain2 = fiddler.save_app({'foo.py': 'new text'}, fiddle_id=subdomain)
        eq_(subdomain2, subdomain)
        files = fiddler.get_files(subdomain)
        eq_(files, dict([('foo.py', 'new text')]))

    def test_delete_file(self):
        status, app_id = fiddler.save_app({'foo': 'bar baz', 'asd.py': 'omg2'})
        files = fiddler.get_files(app_id)
        eq_(files, dict([('foo', 'bar baz'), ('asd.py', 'omg2')]))

        fiddler.save_app({}, {'asd.py': 1}, fiddle_id=app_id)
        files = fiddler.get_files(app_id)
        eq_(files, dict([('foo', 'bar baz')]))
