import pytest

from url_list import urls_per_domain

def test_url_list(url_list):
    assert len(url_list) == 9

    result = urls_per_domain(url_list)

    assert set(result.keys()) == {'domain1.example.com', 'domain2.example.com', 'domain3.example.com'}

    assert result['domain1.example.com'] == {
        "http://domain1.example.com/image.jpg",
        "https://domain1.example.com/image.jpg",
        "https://domain1.example.com/large_image.jpg",
        "https://domain1.example.com/path/image.jpg",
    }
    assert result['domain2.example.com'] == {
        "https://domain2.example.com/image.jpg",
    }
    assert result['domain3.example.com'] == {
        "https://domain3.example.com/image.jpg",
        "https://domain3.example.com/image2.jpg",
        "https://domain3.example.com/image3.jpg",
        "https://domain3.example.com/image4.jpg",
    }
