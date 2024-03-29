#!/usr/bin/env python3
import os
import re
import subprocess
import sys
import time

# get version without importing
with open("django_tables2/__init__.py", "rb") as f:
    VERSION = str(re.search('__version__ = "(.+?)"', f.read().decode()).group(1))

if sys.argv[-1] == "publish":
    try:
        import twine  # noqa
        import wheel  # noqa
    except ImportError:
        print("Required to publish: pip install wheel twine")
    os.system("python setup.py clean --all")
    os.system("python setup.py sdist bdist_wheel --universal")
    os.system(
        f"twine upload dist/django-tables2-{VERSION}.tar.gz"
        f" dist/django_tables2-{VERSION}-py2.py3-none-any.whl"
    )
    print(f"\nreleased [{VERSION}](https://pypi.org/project/django-tables2/{VERSION}/)")
    sys.exit()

if sys.argv[-1] == "tag":
    os.system(f"git tag -a v{VERSION} -m 'tagging v{VERSION}'")
    os.system("git push --tags && git push origin master")
    sys.exit()

if sys.argv[-1] == "screenshots":

    def screenshot(url, filename="screenshot.png", delay=2):
        print(f"Making screenshot of url: {url}")
        chrome = subprocess.Popen(
            ["chromium-browser", "--incognito", "--headless", "--screenshot", url], close_fds=False
        )
        print(f"Starting to sleep for {delay}s...")
        time.sleep(delay)
        chrome.kill()
        os.system(f"convert screenshot.png -trim -bordercolor White -border 10x10 {dest}")
        os.remove("screenshot.png")
        print(f"Saved file to {dest}")

    images = {
        "{url}/tutorial/": "docs/img/example.png",
        "{url}/bootstrap/": "docs/img/bootstrap.png",
        "{url}/bootstrap4/": "docs/img/bootstrap4.png",
        "{url}/semantic/": "docs/img/semantic.png",
    }

    print(
        "Make sure the devserver is running: \n  cd example/\n  PYTHONPATH=.. ./manage.py runserver  --insecure\n\n"
    )

    for url, dest in images.items():
        screenshot(url.format(url="http://localhost:8000"), dest)

    sys.exit()
