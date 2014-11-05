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
        status, subdomain = fiddler.save_app({'foo.py': 'bar baz'})
        files = fiddler.get_code(subdomain)
        eq_(files, [('/appcode_1/foo.py', 'bar baz')])

        # overwrite
        status2, subdomain2 = fiddler.save_app({'foo.py': 'new text'}, subdomain=subdomain)
        eq_(subdomain2, subdomain)
        files = fiddler.get_code(subdomain)
        eq_(files, [('/appcode_1/foo.py', 'new text')])
