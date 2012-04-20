# -*- coding: utf8 -*-
from setuptools import setup, find_packages


setup(
    name='django-attest',
    version='0.2.5.dev',
    description = 'Provides Django specific testing helpers to Attest',

    author='Bradley Ayers',
    author_email='bradley.ayers@gmail.com',
    license='Simplified BSD',
    url='https://github.com/bradleyayers/django-attest/',

    packages=['django_attest'],
    install_requires=['Django >=1.1', 'Attest >=0.5', 'distribute'],

    test_loader='tests:loader',
    test_suite='tests.everything',

    classifiers = [
        'Environment :: Web Environment',
        'Framework :: Django',
        'Intended Audience :: Developers',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Internet :: WWW/HTTP',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ],
)
