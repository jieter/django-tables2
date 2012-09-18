#!/usr/bin/env python
import re
from setuptools import setup, find_packages


with open('django_tables2/__init__.py', 'rb') as f:
    version = re.search('__version__ = "(.+?)"', f.read()).group(1)


setup(
    name='django-tables2',
    version=version,
    description='Table/data-grid framework for Django',

    author='Bradley Ayers',
    author_email='bradley.ayers@gmail.com',
    license='Simplified BSD',
    url='https://github.com/bradleyayers/django-tables2/',

    packages=find_packages(exclude=['tests.*', 'tests', 'example.*', 'example']),
    include_package_data=True,  # declarations in MANIFEST.in

    install_requires=['Django >=1.2'],
    tests_require=['Django >=1.2', 'django-attest >=0.6.0', 'fudge', 'pylint',
                   'django-haystack', 'unittest-xml-reporting', 'lxml', 'pytz'],

    test_loader='tests:loader',
    test_suite='tests.everything',

    classifiers=[
        'Environment :: Web Environment',
        'Framework :: Django',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Internet :: WWW/HTTP',
        'Topic :: Software Development :: Libraries',
    ],
)
