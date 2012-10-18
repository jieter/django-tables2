# coding: utf8
from setuptools import setup


setup(
    name='django-attest',
    version='0.9.1',
    description='Provides Django specific testing helpers to Attest',

    author='Bradley Ayers',
    author_email='bradley.ayers@gmail.com',
    license='Simplified BSD',
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
