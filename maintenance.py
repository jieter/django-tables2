#!/usr/bin/env python3
import os
import subprocess
import sys
import time

try:
    import hatch  # noqa
except ImportError:
    print("Package `hatch` is required: pip install hatch")
    sys.exit()

VERSION = subprocess.check_output(["hatch version"], shell=True).decode().strip()

if sys.argv[-1] == "bump":
    os.system("hatch version patch")

elif sys.argv[-1] == "publish":
    os.system("hatch publish")
    os.system("rm -f dist/django_tables2-2.7.4*")

elif sys.argv[-1] == "tag":
    os.system("hatch build")
    tag_cmd = f"git tag -a v{VERSION} -m 'tagging v{VERSION}'"
    if exitcode := os.system(tag_cmd):
        print(f"Failed tagging with command: {tag_cmd}")
    else:
        os.system("git push --tags && git push origin master")

elif sys.argv[-1] == "screenshots":

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
else:
    print(f"Current version: {VERSION}")
