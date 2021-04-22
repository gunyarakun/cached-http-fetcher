import logging
from email.utils import formatdate

from cached_http_fetcher.content import (
    calc_expired_at,
    parse_cache_control,
    put_content,
)
from cached_http_fetcher.model import FetchedResponse
from cached_http_fetcher.storage import ContentMemoryStorage
from requests import Response
from requests.structures import CaseInsensitiveDict


def test_parse_cache_control() -> None:
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


def test_calc_expired_at() -> None:
    now = 1617355068
    min_cache_age = 47387

    # Cache-Control: no-store
    expired_at = calc_expired_at(
        CaseInsensitiveDict({"cache-control": "no-store"}), now, min_cache_age
    )
    assert now + min_cache_age <= expired_at <= now + min_cache_age * 2

    # Cache-Control: max-age=xxxxx, larger than min_cache_age
    max_age = min_cache_age + 4346
    expired_at = calc_expired_at(
        CaseInsensitiveDict({"cache-control": f"max-age={max_age}"}), now, min_cache_age
    )
    assert now + min_cache_age <= expired_at <= now + min_cache_age * 2

    # Cache-Control: max-age=xxxxx, smaller than min_cache_age
    max_age = min_cache_age - 4346
    expired_at = calc_expired_at(
        CaseInsensitiveDict({"cache-control": f"max-age={max_age}"}), now, min_cache_age
    )
    assert now + min_cache_age <= expired_at <= now + min_cache_age * 2

    # Expires: <now on RFC 2822>
    expired_at = calc_expired_at(
        CaseInsensitiveDict({"expires": formatdate(now)}), now, min_cache_age
    )
    assert now + min_cache_age <= expired_at <= now + min_cache_age * 2

    # Expires: <future on RFC 2822>
    expires = now + min_cache_age + 434553
    expired_at = calc_expired_at(
        CaseInsensitiveDict({"expires": formatdate(expires)}), now, min_cache_age
    )
    assert now + min_cache_age <= expired_at <= expires


def test_put_content(logger: logging.Logger) -> None:
    now = 1617355068
    min_cache_age = 47387
    content_max_age = 5487
    url = "http://example.com/image1.jpg"
    content = b"test content"

    content_storage = ContentMemoryStorage()
    content_storage_dict = content_storage.dict_for_debug()

    # No content type
    response = Response()
    response.url = url
    response.status_code = 200
    response._content_consumed = True
    response._content = content
    meta = put_content(
        FetchedResponse(url, now, response, None),
        min_cache_age,
        content_max_age,
        content_storage,
        logger=logger,
    )
    assert len(content_storage_dict) == 1
    assert content_storage_dict[url].value == content
    assert content_storage_dict[url].content_type is None
    assert content_storage_dict[url].cache_control == f"max-age={content_max_age}"
    assert meta is not None
    assert meta.cached_url == content_storage.cached_url(url)
    assert meta.etag is None
    assert meta.last_modified is None
    assert meta.fetched_at == now
    assert meta.expired_at is not None  # tested in test_calc_expired_at()

    # With content type
    response = Response()
    response.url = url
    response.status_code = 200
    response.headers["Content-Type"] = "image/jpeg"
    meta = put_content(
        FetchedResponse(url, now, response, None),
        min_cache_age,
        content_max_age,
        content_storage,
        logger=logger,
    )
    assert meta is not None
    assert content_storage_dict[url].content_type == "image/jpeg"

    # With etag
    etag = "test etag"
    response = Response()
    response.url = url
    response.status_code = 200
    response.headers["ETag"] = etag
    meta = put_content(
        FetchedResponse(url, now, response, meta),
        min_cache_age,
        content_max_age,
        content_storage,
        logger=logger,
    )
    assert meta is not None
    assert meta.etag == etag

    # With last-modified
    last_modified = "Wed, 21 Oct 2015 07:28:00 GMT"
    response = Response()
    response.url = url
    response.status_code = 200
    response.headers["Last-Modified"] = last_modified
    meta = put_content(
        FetchedResponse(url, now, response, meta),
        min_cache_age,
        content_max_age,
        content_storage,
        logger=logger,
    )
    assert meta is not None
    assert meta.last_modified == last_modified

    # 304
    content_storage = ContentMemoryStorage()
    content_storage_dict = content_storage.dict_for_debug()
    response = Response()
    response.url = url
    response.status_code = 304
    meta = put_content(
        FetchedResponse(url, now, response, meta),
        min_cache_age,
        content_max_age,
        content_storage,
        logger=logger,
    )
    assert meta is not None
    assert len(content_storage_dict) == 0  # Not saved
    assert meta.cached_url == content_storage.cached_url(url)

    # 500
    content_storage = ContentMemoryStorage()
    content_storage_dict = content_storage.dict_for_debug()
    response = Response()
    response.url = url
    response.status_code = 500
    meta = put_content(
        FetchedResponse(url, now, response, None),
        min_cache_age,
        content_max_age,
        content_storage,
        logger=logger,
    )
    assert meta is None
    assert len(content_storage_dict) == 0  # Not saved
