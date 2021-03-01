from typing import Iterable

import os
import sys
import pytest

sys.path.append(os.path.abspath(os.path.dirname(os.path.abspath(__file__)) + "/../src/"))

@pytest.fixture(scope="session", autouse=True)
def url_list() -> Iterable[str]:
    return {
        "http://domain1.example.com/image.jpg",
        "https://domain1.example.com/image.jpg",
        "https://domain1.example.com/path/image.jpg",
        "https://domain2.example.com/image.jpg",
        "https://domain3.example.com/image.jpg",
        "https://domain3.example.com/image2.jpg",
        "https://domain3.example.com/image3.jpg",
        "https://domain3.example.com/image4.jpg",
    }
