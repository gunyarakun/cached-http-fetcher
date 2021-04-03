import hashlib
import os
import sys
from logging import DEBUG, StreamHandler, getLogger
from typing import Iterable

import pytest
import responses as responses_

sys.path.append(
    os.path.abspath(os.path.dirname(os.path.abspath(__file__)) + "/../src/")
)

URLS = {
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

for url, obj in URLS.items():
    obj["content"] = hashlib.sha256(url.encode("utf-8")).hexdigest()


@pytest.fixture(scope="session", autouse=True)
def url_list() -> Iterable[str]:
    return URLS.keys()


@pytest.fixture(scope="session", autouse=True)
def urls():
    return URLS


@pytest.fixture(scope="session", autouse=True)
def logger() -> Iterable[str]:
    log = getLogger(__name__)
    handler = StreamHandler()
    handler.setLevel(DEBUG)
    log.setLevel(DEBUG)
    log.addHandler(handler)
    log.propagate = False

    return log


@pytest.fixture(scope="function")
def requests_mock():
    with responses_.RequestsMock() as r:
        yield r
