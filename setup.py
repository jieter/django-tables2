#!/usr/bin/env python
from setuptools import setup, find_packages


setup(
    name='django-tables',
    version='0.4.0.alpha2.dev',
    description='Table framework for Django',

    author='Bradley Ayers',
    author_email='bradley.ayers@gmail.com',
    license='Simplified BSD',
    url='https://github.com/bradleyayers/django-tables/',

    packages=find_packages(),
    include_package_data=True,  # declarations in MANIFEST.in

    install_requires=['Django >=1.1'],

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
