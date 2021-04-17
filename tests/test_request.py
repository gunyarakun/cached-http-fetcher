import logging

import responses
from cached_http_fetcher.model import Meta
from cached_http_fetcher.request import cached_requests_get


def test_cached_requests_get(
    requests_mock: responses.RequestsMock, logger: logging.Logger
) -> None:
    now = 1617355068
    past = now - 3600
    future = now + 3600
    url = "https://example.com/image1.txt"
    requests_mock.add(requests_mock.GET, url, body=b"test")

    # fetch without meta
    fetched_response = cached_requests_get(url, None, now, logger=logger)
    assert fetched_response is not None
    assert len(requests_mock.calls) == 1
    assert fetched_response.url == url
    assert fetched_response.fetched_at == now
    assert fetched_response.response.status_code == 200
    assert fetched_response.response.content == b"test"
    last_call = requests_mock.calls[-1]
    assert "If-None-Match" not in last_call.request.headers
    assert "If-Modified-Since" not in last_call.request.headers

    # fetch with non expired meta
    meta = Meta(
        cached_url=url,
        etag=None,
        last_modified=None,
        content_sha1=None,
        fetched_at=past,
        expired_at=future,
    )
    fetched_response = cached_requests_get(url, meta, now, logger=logger)
    assert fetched_response is None

    # fetch with expired meta including etag
    meta = Meta(
        cached_url=url,
        etag="deadbeef",
        last_modified=None,
        content_sha1=None,
        fetched_at=past,
        expired_at=past,
    )
    fetched_response = cached_requests_get(url, meta, now, logger=logger)
    assert fetched_response is not None
    assert len(requests_mock.calls) == 2
    assert fetched_response.url == url
    assert fetched_response.fetched_at == now
    assert fetched_response.response.status_code == 200
    assert fetched_response.response.content == b"test"
    last_call = requests_mock.calls[-1]
    assert last_call.request.headers["If-None-Match"] == meta.etag
    assert "If-Modified-Since" not in last_call.request.headers

    # fetch with expired meta including last_modified
    meta = Meta(
        cached_url=url,
        etag=None,
        last_modified="Wed, 21 Oct 2015 07:28:00 GMT",
        content_sha1=None,
        fetched_at=past,
        expired_at=past,
    )
    fetched_response = cached_requests_get(url, meta, now, logger=logger)
    assert fetched_response is not None
    assert len(requests_mock.calls) == 3
    assert fetched_response.url == url
    assert fetched_response.fetched_at == now
    assert fetched_response.response.status_code == 200
    assert fetched_response.response.content == b"test"
    last_call = requests_mock.calls[-1]
    assert "If-None-Match" not in last_call.request.headers
    assert last_call.request.headers["If-Modified-Since"] == meta.last_modified


# TODO: test_requests_get()
