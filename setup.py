#!/usr/bin/env python
from setuptools import setup, find_packages


setup(
    name='django-tables2',
    version='0.13.0',
    description='Table/data-grid framework for Django',

    author='Bradley Ayers',
    author_email='bradley.ayers@gmail.com',
    license='Simplified BSD',
    url='https://github.com/bradleyayers/django-tables2/',

    packages=find_packages(exclude=['tests.*', 'tests', 'example.*', 'example']),
    include_package_data=True,  # declarations in MANIFEST.in

    install_requires=['Django >=1.3'],
    tests_require=['Django >=1.3', 'django-attest >=0.5.0', 'fudge', 'pylint',
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
