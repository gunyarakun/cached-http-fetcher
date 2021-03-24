from typing import Iterable

import io
import os
import sys
import pytest
import hashlib
from PIL import Image
import responses as responses_
from logging import getLogger, StreamHandler, DEBUG

sys.path.append(os.path.abspath(os.path.dirname(os.path.abspath(__file__)) + "/../src/"))

IMAGES = {
    "http://domain1.example.com/image.jpg": {
        "width": 100,
        "height": 100,
        "format": "JPEG",
    },
    "https://domain1.example.com/image.jpg": {
        "width": 100,
        "height": 100,
        "format": "JPEG",
    },
    "https://domain1.example.com/large_image.jpg": {
        "width": 2000,
        "height": 2000,
        "format": "JPEG",
    },
    "https://domain1.example.com/path/image.jpg": {
        "width": 100,
        "height": 100,
        "format": "JPEG",
    },
    "https://domain2.example.com/image.jpg": {
        "width": 100,
        "height": 100,
        "format": "JPEG",
    },
    "https://domain3.example.com/image.jpg": {
        "width": 100,
        "height": 100,
        "format": "JPEG",
    },
    "https://domain3.example.com/image2.jpg": {
        "width": 100,
        "height": 100,
        "format": "JPEG",
    },
    "https://domain3.example.com/image3.jpg": {
        "width": 100,
        "height": 100,
        "format": "JPEG",
    },
    "https://domain3.example.com/image4.jpg": {
        "width": 100,
        "height": 100,
        "format": "JPEG",
    },
}

# create images
for url, obj in IMAGES.items():
    # generate color from url
    color = int(hashlib.sha256(url.encode('utf-8')).hexdigest(), 16) % 0xffffff

    img = Image.new("RGB", (obj["width"], obj["height"]), color=color)
    with io.BytesIO() as output:
        img.save(output, format=obj["format"])
        obj["image"] = output.getvalue()


@pytest.fixture(scope="session", autouse=True)
def url_list() -> Iterable[str]:
    return IMAGES.keys()


# TODO: type hint
@pytest.fixture(scope="session", autouse=True)
def images():
    return IMAGES


@pytest.fixture(scope="session", autouse=True)
def logger() -> Iterable[str]:
    l = getLogger(__name__)
    handler = StreamHandler()
    handler.setLevel(DEBUG)
    l.setLevel(DEBUG)
    l.addHandler(handler)
    l.propagate = False

    return l


@pytest.fixture(scope="function")
def requests_mock():
    with responses_.RequestsMock() as r:
        yield r
