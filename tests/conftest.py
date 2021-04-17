import hashlib
import os
import sys
from logging import DEBUG, Logger, StreamHandler, getLogger
from typing import Dict, Generator, Iterable, Optional

import pytest
import responses as responses_

from .model import FixtureURLContent, FixtureURLS

sys.path.append(
    os.path.abspath(os.path.dirname(os.path.abspath(__file__)) + "/../src/")
)


URLS: FixtureURLS = {
    "http://domain1.example.com/image.jpg": FixtureURLContent(),
    "https://domain1.example.com/image.jpg": FixtureURLContent(),
    "https://domain1.example.com/large_image.jpg": FixtureURLContent(),
    "https://domain1.example.com/path/image.jpg": FixtureURLContent(),
    "https://domain2.example.com/image.jpg": FixtureURLContent(),
    "https://domain3.example.com/image.jpg": FixtureURLContent(),
    "https://domain3.example.com/image2.jpg": FixtureURLContent(),
    "https://domain3.example.com/image3.jpg": FixtureURLContent(),
    "https://domain3.example.com/image4.jpg": FixtureURLContent(),
}


@pytest.fixture(scope="session", autouse=True)
def url_list() -> Iterable[str]:
    return URLS.keys()


@pytest.fixture(scope="session", autouse=True)
def urls() -> FixtureURLS:
    return URLS


@pytest.fixture(scope="session", autouse=True)
def logger() -> Logger:
    log = getLogger(__name__)
    handler = StreamHandler()
    handler.setLevel(DEBUG)
    log.setLevel(DEBUG)
    log.addHandler(handler)
    log.propagate = False

    return log


@pytest.fixture(scope="function")
def requests_mock() -> Generator[responses_.RequestsMock, None, None]:
    with responses_.RequestsMock() as r:
        yield r
