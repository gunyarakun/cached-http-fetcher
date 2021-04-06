import pytest
from cached_http_fetcher.entrypoint import fetch_urls_single, fetch_urls
from cached_http_fetcher.meta import get_meta
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
        meta = get_meta(
            url, meta_storage=meta_memory_storage, logger=logger
        )
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


@pytest.mark.skip(reason="not working well")
def test_fetch_urls_memory(urls, logger, requests_mock):
    # Almost all logics are tested in test_fetch_urls_single
    for url, obj in urls.items():
        requests_mock.add(requests_mock.GET, url, body=obj["content"])

    url_list = urls.keys()

    meta_memory_storage = MemoryStorage()
    content_memory_storage = ContentMemoryStorage()

    fetch_urls(
        url_list,
        meta_storage=meta_memory_storage,
        content_storage=content_memory_storage,
        min_cache_age=7200,
        content_max_age=3600,
        num_fetch_processes=1,
        num_content_processes=1,
        logger=logger,
    )

    meta_storage = meta_memory_storage.dict_for_debug()
    content_storage = content_memory_storage.dict_for_debug()

    assert len(requests_mock.calls) == len(urls)
    assert len(meta_storage) == len(urls)
    assert len(content_storage) == len(urls)
