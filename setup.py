#!/usr/bin/env python
import os
import re
import sys

from setuptools import find_packages, setup

# get version without importing
with open('django_tables2/__init__.py', 'rb') as f:
    VERSION = str(re.search('__version__ = \'(.+?)\'', f.read().decode('utf-8')).group(1))

if sys.argv[-1] == 'publish':
    os.system('python setup.py sdist upload')
    print('\nreleased [{version}](https://pypi.python.org/pypi/django-tables2/{version})'.format(version=VERSION))
    sys.exit()

if sys.argv[-1] == 'tag':
    os.system("git tag -a v{} -m 'tagging v{}'".format(VERSION, VERSION))
    os.system('git push --tags && git push origin master')
    sys.exit()


setup(
    name='django-tables2',
    version=VERSION,
    description='Table/data-grid framework for Django',

    author='Bradley Ayers',
    author_email='bradley.ayers@gmail.com',
    license='Simplified BSD',
    url='https://github.com/bradleyayers/django-tables2/',

    packages=find_packages(exclude=['tests.*', 'tests', 'example.*', 'example']),
    include_package_data=True,  # declarations in MANIFEST.in

    install_requires=['Django>=1.8'],

    classifiers=[
        'Environment :: Web Environment',
        'Framework :: Django',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Topic :: Internet :: WWW/HTTP',
        'Topic :: Software Development :: Libraries',
    ],
)
