import pytest

@pytest.fixture(scope="session", autouse=True)
def url_list():
    return [
        "http://domain1.example.com/image.jpg",
        "https://domain1.example.com/image.jpg",
        "https://domain1.example.com/path/image.jpg",
        "https://domain2.example.com/image.jpg",
        "https://domain3.example.com/image.jpg",
        "https://domain3.example.com/image2.jpg",
        "https://domain3.example.com/image3.jpg",
        "https://domain3.example.com/image4.jpg",
    ]
