<<<<<<< HEAD
#!/usr/bin/env python
import re
from setuptools import setup, find_packages


with open('django_tables2/__init__.py', 'rb') as f:
    version = str(re.search('__version__ = "(.+?)"', f.read().decode('utf-8')).group(1))


setup(
    name='django-tables2',
    version=version,
    description='Table/data-grid framework for Django',
=======
# coding: utf8
from setuptools import setup


setup(
    name='django-attest',
    version='0.10.0',
    description='Provides Django specific testing helpers to Attest',
>>>>>>> upstream/master

    author='Bradley Ayers',
    author_email='bradley.ayers@gmail.com',
    license='Simplified BSD',
<<<<<<< HEAD
    url='https://github.com/bradleyayers/django-tables2/',

    packages=find_packages(exclude=['tests.*', 'tests', 'example.*', 'example']),
    include_package_data=True,  # declarations in MANIFEST.in

    install_requires=['Django >=1.2', 'six'],

    test_loader='tests:loader',
    test_suite='tests.everything',
=======
    url='https://github.com/bradleyayers/django-attest/',

    packages=['django_attest'],
    install_requires=['Django >=1.2', 'Attest >=0.6dev', 'distribute', 'six'],
    use_2to3=True,

    entry_points={
        'attest.reporters': [
            'django-xml = django_attest:XmlReporter',
            'django-xunit = django_attest:XUnitReporter',
            'django-quickfix = django_attest:QuickFixReporter',
            'django-plain = django_attest:PlainReporter',
            'django-fancy = django_attest:FancyReporter',
            'django = django_attest:auto_reporter',
        ],
    },
>>>>>>> upstream/master

    classifiers=[
        'Environment :: Web Environment',
        'Framework :: Django',
        'Intended Audience :: Developers',
<<<<<<< HEAD
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Topic :: Internet :: WWW/HTTP',
        'Topic :: Software Development :: Libraries',
=======
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Internet :: WWW/HTTP',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
        'Topic :: Software Development :: Libraries :: Python Modules',
>>>>>>> upstream/master
    ],
)
