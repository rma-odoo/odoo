#!/usr/bin/env python
# -*- coding: utf-8 -*-
from setuptools import find_packages, setup
from os.path import join, dirname


execfile(join(dirname(__file__), 'openerp', 'release.py'))  # Load release variables
lib_name = 'openerp'
setup(
    name='openerp',
    version=version,
    description=description,
    long_description=long_desc,
    url=url,
    author=author,
    author_email=author_email,
    classifiers=filter(None, classifiers.split('\n')),
    license=license,
    scripts=['openerp-server', 'openerp-gevent', 'odoo.py'],
    # Full packaging:
    packages=find_packages(),
    package_dir={'%s' % lib_name: 'openerp'},
    include_package_data=True,
    dependency_links=['http://download.gna.org/pychart/'],
    install_requires=[
        'babel >= 1.0',
        'decorator',
        'docutils',
        'feedparser',
        'gevent',
        'Jinja2',
        'lxml',  # windows binary http://www.lfd.uci.edu/~gohlke/pythonlibs/
        'mako',
        'mock',
        'passlib',
        'pillow',  # windows binary http://www.lfd.uci.edu/~gohlke/pythonlibs/
        'psutil',  # windows binary code.google.com/p/psutil/downloads/list
        'psycogreen',
        'psycopg2 >= 2.2',
        'pychart',  # not on pypi, use: pip install http://download.gna.org/pychart/PyChart-1.39.tar.gz
        'pydot',
        'pyparsing < 2',
        'pypdf',
        'pyserial',
        'python-dateutil',
        'python-ldap',  # optional
        'python-openid',
        'pytz',
        'pyusb >= 1.0.0b1',
        'pyyaml',
        'qrcode',
        'reportlab',  # windows binary pypi.python.org/pypi/reportlab
        'requests',
        'simplejson',
        'unittest2',
        'vatnumber',
        'vobject',
        'werkzeug',
        'xlwt',
    ],
    extras_require={
        'SSL': ['pyopenssl'],
    },
    tests_require=[
        'unittest2',
        'mock',
    ],
)
