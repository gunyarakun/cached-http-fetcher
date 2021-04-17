import logging

from cached_http_fetcher.model import FetchedResponse, Meta
from cached_http_fetcher.rate_limit_fetcher import RateLimitFetcher
from pytest_mock import MockerFixture
from requests import Response


def test_rate_limit_fetcher(mocker: MockerFixture, logger: logging.Logger) -> None:
    now = 1617355068
    past = now - 3600
    future = now + 3600
    url = "http://example.com/image1.jpg"
    mock_fetched_response = FetchedResponse(
        url=url, fetched_at=now, response=Response(), old_meta=None
    )

    mock = mocker.patch(
        "cached_http_fetcher.rate_limit_fetcher.cached_requests_get",
        return_value=mock_fetched_response,
    )

    # No rate limit
    rate_limit_fetcher = RateLimitFetcher(
        max_fetch_count=0, fetch_count_window=0, logger=logger
    )
    old_meta = Meta(
        cached_url=url,
        etag=None,
        last_modified=None,
        content_sha1=None,
        fetched_at=past,
        expired_at=future,
    )
    for fetched_response in rate_limit_fetcher.fetch(url, old_meta, now):
        assert fetched_response == mock_fetched_response
    mock.assert_called_once()
    call_args = mock.call_args[0]
    print(call_args)
    assert call_args[0] == url
    assert call_args[1] == old_meta
    assert call_args[2] == now
