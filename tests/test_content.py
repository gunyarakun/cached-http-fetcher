from requests import Response
from email.utils import formatdate
from requests.structures import CaseInsensitiveDict

from cached_http_fetcher.storage import ContentMemoryStorage
from cached_http_fetcher.content import put_content, parse_cache_control, calc_expired_at


def test_parse_cache_control():
    directives = parse_cache_control("no-cache")
    assert "no-cache" in directives
    assert directives["no-cache"] is None

    directives = parse_cache_control("max-age=12345")
    assert "max-age" in directives
    assert directives["max-age"] == "12345"

    directives = parse_cache_control("max-stale")
    assert "max-stale" in directives
    assert directives["max-stale"] is None

    directives = parse_cache_control("max-stale=23456")
    assert "max-stale" in directives
    assert directives["max-stale"] == "23456"


def test_calc_expired_at():
    now = 1617355068
    min_cache_age = 47387

    # Cache-Control: no-store
    expired_at = calc_expired_at(CaseInsensitiveDict({"cache-control": "no-store"}), now, min_cache_age)
    assert expired_at == now + min_cache_age

    # Cache-Control: max-age=xxxxx, larger than min_cache_age
    max_age = min_cache_age + 4346
    expired_at = calc_expired_at(CaseInsensitiveDict({"cache-control": f"max-age={max_age}"}), now, min_cache_age)
    assert expired_at == now + max_age

    # Cache-Control: max-age=xxxxx, smaller than min_cache_age
    max_age = min_cache_age - 4346
    expired_at = calc_expired_at(CaseInsensitiveDict({"cache-control": f"max-age={max_age}"}), now, min_cache_age)
    assert expired_at == now + min_cache_age

    # Expires: <now on RFC 2822>
    expired_at = calc_expired_at(CaseInsensitiveDict({"expires": formatdate(now)}), now, min_cache_age)
    assert expired_at == now + min_cache_age

    # Expires: <now on RFC 2822>
    expires = now + min_cache_age + 434553
    expired_at = calc_expired_at(CaseInsensitiveDict({"expires": formatdate(expires)}), now, min_cache_age)
    assert expired_at == expires


def test_put_content():
    now = 1617355068
    min_cache_age = 47387
    content_max_age = 5487
    url = "http://example.com/image1.jpg"
    content = b"test content"

    content_storage = ContentMemoryStorage()
    content_storage_dict = content_storage.dict_for_debug()

    # No content type
    response = Response()
    response.status_code = 200
    response._content_consumed = True
    response._content = content
    parsed_header = put_content(url, response, min_cache_age, content_max_age, now, content_storage)
    assert len(content_storage_dict) == 1
    assert content_storage_dict[url]["value"] == content
    assert content_storage_dict[url]["content_type"] is None
    assert content_storage_dict[url]["cache_control"] == f"max-age={content_max_age}"
    assert parsed_header.etag == None
    assert parsed_header.last_modified == None
    assert parsed_header.expired_at is not None # tested in test_calc_expired_at()

    # With content type
    response = Response()
    response.status_code = 200
    response.headers["Content-Type"] = "image/jpeg"
    parsed_header = put_content(url, response, min_cache_age, content_max_age, now, content_storage)
    assert content_storage_dict[url]["content_type"] == "image/jpeg"

    # With etag
    etag = "test etag"
    response = Response()
    response.status_code = 200
    response.headers["ETag"] = etag
    parsed_header = put_content(url, response, min_cache_age, content_max_age, now, content_storage)
    assert parsed_header.etag == etag

    # With last-modified
    last_modified = "Wed, 21 Oct 2015 07:28:00 GMT"
    response = Response()
    response.status_code = 200
    response.headers["Last-Modified"] = last_modified
    parsed_header = put_content(url, response, min_cache_age, content_max_age, now, content_storage)
    assert parsed_header.last_modified == last_modified
