#!/usr/bin/env python3
import re

from setuptools import find_packages, setup

# get version without importing
with open("django_tables2/__init__.py", "rb") as f:
    VERSION = str(re.search('__version__ = "(.+?)"', f.read().decode()).group(1))

setup(
    name="django-tables2",
    version=VERSION,
    description="Table/data-grid framework for Django",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    author="Bradley Ayers",
    author_email="bradley.ayers@gmail.com",
    license="Simplified BSD",
    url="https://github.com/jieter/django-tables2/",
    packages=find_packages(exclude=["tests.*", "tests", "example.*", "example", "docs"]),
    include_package_data=True,  # declarations in MANIFEST.in
    install_requires=["Django>=1.11"],
    extras_require={"tablib": ["tablib"]},
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Environment :: Web Environment",
        "Framework :: Django",
        "Framework :: Django :: 2.2",
        "Framework :: Django :: 3.1",
        "Framework :: Django :: 3.2",
        "Framework :: Django :: 4.0",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: BSD License",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3 :: Only",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Topic :: Internet :: WWW/HTTP",
        "Topic :: Software Development :: Libraries",
    ],
)
