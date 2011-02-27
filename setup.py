# -*- coding: utf8 -*-
from setuptools import setup, find_packages


setup(
    name='django-attest',
    version='0.1 alpha',
    description = 'Provides Django specific testing helpers to Attest',

    author='Bradley Ayers',
    author_email='bradley.ayers@gmail.com',
    license='Simplified BSD',
    url='https://github.com/bradleyayers/django-attest/',

    packages = find_packages(),

    install_requires=['Attest>=0.4'],

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
