# -*- coding: utf-8 -*-
"""Setup script."""

import os
from setuptools import setup, find_packages

setup(
    name='app',
    version='0.1',
    author="Paul Korzhyk",
    author_email="paul@scifiware.com",
    description="app engine skeleton",
    packages=find_packages('app'),
    package_dir = {'': 'app'},
    include_package_data=True,
    install_requires=[
        'flask',
        'jinja2',
        'werkzeug',
        'werkzeug_debugger_appengine',
        'distribute',
    ],
    zip_safe=False,
)
