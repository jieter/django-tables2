# coding: utf8
from setuptools import setup


setup(
    name='django-attest',
    version='0.8.1',
    description='Provides Django specific testing helpers to Attest',

    author='Bradley Ayers',
    author_email='bradley.ayers@gmail.com',
    license='Simplified BSD',
    url='https://github.com/bradleyayers/django-attest/',

    packages=['django_attest'],
    install_requires=['Django >=1.2', 'Attest >=0.5', 'distribute', 'six'],
    use_2to3=True,

    test_loader='tests:loader',
    test_suite='tests.suite',

    classifiers=[
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
