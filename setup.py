#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys


try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

if sys.argv[-1] == 'publish':
    os.system('python setup.py sdist upload')
    sys.exit()

readme = open('README.rst').read()
history = open('HISTORY.rst').read().replace('.. :changelog:', '')

setup(
    name='signupto',
    version='0.0.6',
    description='sign-up.to API client',
    long_description=readme + '\n\n' + history,
    author='Luke Plant',
    author_email='L.Plant.98@cantab.net',
    url='https://bitbucket.org/spookylukey/signupto',
    packages=[
        'signupto',
    ],
    package_dir={'signupto': 'signupto'},
    include_package_data=True,
    install_requires=[
        "requests >= 2.0",
        "six >= 1.4",
    ],
    license="BSD",
    zip_safe=False,
    keywords='signupto',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Natural Language :: English',
        "Programming Language :: Python :: 2",
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
    ],
    test_suite='tests',
)
