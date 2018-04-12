#!/usr/bin/env python
import os
import re
import subprocess
import sys
import time

# get version without importing
with open('django_tables2/__init__.py', 'rb') as f:
    VERSION = str(re.search('__version__ = \'(.+?)\'', f.read().decode('utf-8')).group(1))

if sys.argv[-1] == 'publish':
    os.system('python setup.py sdist')
    os.system('twine upload dist/django-tables2-{version}.tar.gz'.format(version=VERSION))
    print('\nreleased [{version}](https://pypi.org/project/django-tables2/{version}/)'.format(version=VERSION))
    sys.exit()

if sys.argv[-1] == 'tag':
    os.system("git tag -a v{} -m 'tagging v{}'".format(VERSION, VERSION))
    os.system('git push --tags && git push origin master')
    sys.exit()

if sys.argv[-1] == 'screenshots':

    def screenshot(url, filename='screenshot.png', delay=2):
        print('Making screenshot of url: {}'.format(url))
        chrome = subprocess.Popen(
            ['chromium-browser', '--incognito', '--headless', '--screenshot', url],
            close_fds=False
        )
        print('Starting to sleep for {}s...'.format(delay))
        time.sleep(delay)
        chrome.kill()
        os.system('convert screenshot.png -trim -bordercolor White -border 10x10 {}'.format(dest))
        os.remove('screenshot.png')
        print('Saved file to', dest)

    images = {
        '{url}/tutorial/': 'docs/img/example.png',
        '{url}/bootstrap/': 'docs/img/bootstrap.png',
        '{url}/bootstrap4/': 'docs/img/bootstrap4.png',
        '{url}/semantic/': 'docs/img/semantic.png',
    }

    print('Make sure the devserver is running: \n  cd example/\n  PYTHONPATH=.. ./manage.py runserver  --insecure\n\n')

    for url, dest in images.items():
        screenshot(url.format(url='http://localhost:8000'), dest)

    sys.exit()
