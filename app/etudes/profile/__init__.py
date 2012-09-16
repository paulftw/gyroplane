"""
    User profile
""" 

from flask import Blueprint
import gaesessions
import logging



KEY_DELIMITER = '!'
KEY_PATTERN = '%s' + KEY_DELIMITER + '%s'


def decorate_wsgi_app(wsgi_app, **kwargs):
    return gaesessions.SessionMiddleware(wsgi_app, 
                                         session_class=ProfileSession,
                                         **kwargs)
