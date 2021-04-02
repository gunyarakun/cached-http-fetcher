from cached_http_fetcher.entrypoint import (
    RateLimitFetcher,
    fetch_urls,
    fetch_urls_single,
    get_cached_url,
)
from cached_http_fetcher.storage import ContentMemoryStorage, MemoryStorage


def test_fetch_urls_single_memory(images, logger, requests_mock):
    for url, obj in images.items():
        requests_mock.add(requests_mock.GET, url, body=obj["image"])

    url_list = images.keys()

    meta_memory_storage = MemoryStorage()
    content_memory_storage = ContentMemoryStorage()

    # Not yet cached
    for url in url_list:
        cached_url = get_cached_url(url, meta_storage=meta_memory_storage, logger=logger)
        assert cached_url is None

    fetch_urls_single(
        url_list,
        meta_storage=meta_memory_storage,
        content_storage=content_memory_storage,
        logger=logger,
    )

    meta_storage = meta_memory_storage.dict_for_debug()
    content_storage = content_memory_storage.dict_for_debug()

    assert len(requests_mock.calls) == len(images)
    assert len(meta_storage) == len(images)
    assert len(content_storage) == len(images)

    # get cached urls
    for url in url_list:
        cached_url = get_cached_url(url, meta_storage=meta_memory_storage, logger=logger)
        assert cached_url == content_memory_storage.cached_url(url)

    # all images must be cached
    fetch_urls_single(
        url_list,
        meta_storage=meta_memory_storage,
        content_storage=content_memory_storage,
        logger=logger,
    )

    assert len(requests_mock.calls) == len(images)
    assert len(meta_storage) == len(images)
    assert len(content_storage) == len(images)

    # if meta storage is empty, fetch all images
    meta_memory_storage = MemoryStorage()
    fetch_urls_single(
        url_list,
        meta_storage=meta_memory_storage,
        content_storage=content_memory_storage,
        logger=logger,
    )
    meta_storage = meta_memory_storage.dict_for_debug()
    assert len(requests_mock.calls) == len(images) * 2
    assert len(meta_storage) == len(images)
    assert len(content_storage) == len(images)
