from app.app import app
import unittest
import os
from nose.tools import eq_
from google.appengine.ext import testbed

class AppTestCase(unittest.TestCase):
    
    def setUp(self):
        # Setup AppEngine testbed
        self.testbed = testbed.Testbed()
        self.testbed.activate()
        self.testbed.init_datastore_v3_stub()
        self.testbed.init_memcache_stub()

        root_app = app.instances['']
        root_app.config['TESTING'] = True
        self.client = root_app.test_client()
    
    def test_homepage(self):
        response = self.client.get('/')
        eq_(response.status, '200 OK')
