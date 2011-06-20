# -*- coding: utf-8 -*-
"""Setup script."""

import os
from setuptools import setup, find_packages

setup(
    name='lounge',
    version='0.1',
    author="Paul Korzhyk",
    author_email="paul@scifiware.com",
    description=("app engine lounge"),
    license="Proprietary. This code has been stolen.",
    classifiers=[
        'Programming Language :: Python',
        'Topic :: Internet :: WWW/HTTP',
        'Topic :: Internet :: WWW/HTTP :: WSGI :: Server',
        ],
    url='',
    packages=find_packages(exclude = [
        "bin",
        "gae_libs",
        "tests",
        ]),
    package_dir = {'': '.'},
    include_package_data=True,
    install_requires=[
        'flask',
        'distribute'
    ],
    zip_safe=False,
)
