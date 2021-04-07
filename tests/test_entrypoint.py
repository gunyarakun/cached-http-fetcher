import multiprocessing

import cached_http_fetcher.entrypoint
import pytest
from cached_http_fetcher import Meta
from cached_http_fetcher.entrypoint import (
    FetchWorker,
    fetch_urls,
    fetch_urls_single,
    url_queue_from_iterable,
)
from cached_http_fetcher.meta import get_meta
from cached_http_fetcher.rate_limit_fetcher import RateLimitFetcher
from cached_http_fetcher.storage import ContentMemoryStorage, MemoryStorage


def test_fetch_urls_single_memory(urls, logger, requests_mock):
    for url, obj in urls.items():
        requests_mock.add(requests_mock.GET, url, body=obj["content"])

    url_list = urls.keys()

    meta_memory_storage = MemoryStorage()
    content_memory_storage = ContentMemoryStorage()

    # Not yet cached
    for url in url_list:
        meta = get_meta(url, meta_storage=meta_memory_storage, logger=logger)
        assert meta is None

    fetch_urls_single(
        url_list,
        meta_storage=meta_memory_storage,
        content_storage=content_memory_storage,
        logger=logger,
    )

    meta_storage = meta_memory_storage.dict_for_debug()
    content_storage = content_memory_storage.dict_for_debug()

    assert len(requests_mock.calls) == len(urls)
    assert len(meta_storage) == len(urls)
    assert len(content_storage) == len(urls)

    # get cached urls
    for url in url_list:
        meta = get_meta(url, meta_storage=meta_memory_storage, logger=logger)
        assert meta.cached_url == content_memory_storage.cached_url(url)

    # all responses must be cached
    fetch_urls_single(
        url_list,
        meta_storage=meta_memory_storage,
        content_storage=content_memory_storage,
        logger=logger,
    )

    assert len(requests_mock.calls) == len(urls)
    assert len(meta_storage) == len(urls)
    assert len(content_storage) == len(urls)

    # if meta storage is empty, fetch all
    meta_memory_storage = MemoryStorage()
    fetch_urls_single(
        url_list,
        meta_storage=meta_memory_storage,
        content_storage=content_memory_storage,
        logger=logger,
    )
    meta_storage = meta_memory_storage.dict_for_debug()
    assert len(requests_mock.calls) == len(urls) * 2
    assert len(meta_storage) == len(urls)
    assert len(content_storage) == len(urls)


def test_fetch_worker(url_list, mocker, logger):
    url_queue = url_queue_from_iterable(url_list, logger)
    response_queue = multiprocessing.Queue()
    url_queue.put(None)

    meta_memory_storage = MemoryStorage()

    max_fetch_count = 12741
    fetch_count_window = 548583

    meta = Meta(
        cached_url="dummy",
        etag=None,
        last_modified=None,
        content_sha1=None,
        fetched_at=0,
        expired_at=0,
    )

    mock_get_valid_meta = mocker.patch(
        "cached_http_fetcher.entrypoint.get_valid_meta", return_value=meta
    )
    mock_rate_limit_fetcher = mocker.patch(
        "cached_http_fetcher.entrypoint.RateLimitFetcher"
    )

    fw = FetchWorker(
        url_queue,
        response_queue,
        meta_memory_storage,
        max_fetch_count,
        fetch_count_window,
    )
    fw.run()
    fw.close()
    assert mock_get_valid_meta.call_count == len(url_list)
    mock_rate_limit_fetcher.assert_called_once()
    assert len(mock_rate_limit_fetcher.mock_calls) == len(url_list) * 2 + 1


def test_content_worker():
    # TODO:
    pass


@pytest.mark.skip(reason="not working well")
def test_fetch_urls_memory(urls, logger, requests_mock):
    # Almost all logics are tested in test_fetch_urls_single
    for url, obj in urls.items():
        requests_mock.add(requests_mock.GET, url, body=obj["content"])

    url_list = urls.keys()

    meta_memory_storage = MemoryStorage()
    content_memory_storage = ContentMemoryStorage()

    # No rate limit
    fetch_urls(
        url_list,
        meta_storage=meta_memory_storage,
        content_storage=content_memory_storage,
        rate_limit_count=0,
        rate_limit_seconds=0,
        min_cache_age=7200,
        content_max_age=3600,
        num_fetch_processes=1,
        num_content_processes=1,
        logger=logger,
    )

    meta_storage = meta_memory_storage.dict_for_debug()
    content_storage = content_memory_storage.dict_for_debug()

    assert requests_mock.call_count == len(urls)
    assert len(meta_storage) == len(urls)
    assert len(content_storage) == len(urls)

    meta_memory_storage = MemoryStorage()

    # With rate limit 1call/1sec
    fetch_urls(
        url_list,
        meta_storage=meta_memory_storage,
        content_storage=content_memory_storage,
        rate_limit_count=1,
        rate_limit_seconds=1,
        min_cache_age=7200,
        content_max_age=3600,
        num_fetch_processes=1,
        num_content_processes=1,
        logger=logger,
    )
