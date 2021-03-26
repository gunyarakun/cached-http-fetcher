import pytest

from url_list import urls_per_domain
from fetcher import fetch_urls, fetch_urls_single
from storage import MemoryStorage, ContentMemoryStorage


def test_fetch_urls_single_memory(images, logger, requests_mock):
    for url, obj in images.items():
        requests_mock.add(
            requests_mock.GET, url, body=obj['image']
        )

    url_dict = urls_per_domain(images.keys())

    meta_memory_storage = MemoryStorage()
    content_memory_storage = ContentMemoryStorage()

    fetch_urls_single(url_dict, meta_storage=meta_memory_storage, cache_storage=content_memory_storage, logger=logger)

    meta_storage = meta_memory_storage.dict_for_debug()
    cache_storage = content_memory_storage.dict_for_debug()

    assert len(requests_mock.calls) == len(images)
    assert len(meta_storage) == len(images)
    assert len(cache_storage) == len(images)

    # all images must be cached
    fetch_urls_single(url_dict, meta_storage=meta_memory_storage, cache_storage=content_memory_storage, logger=logger)

    assert len(requests_mock.calls) == len(images)
    assert len(meta_storage) == len(images)
    assert len(cache_storage) == len(images)

    # if meta storage is empty, fetch all images
    meta_memory_storage = MemoryStorage()
    fetch_urls_single(url_dict, meta_storage=meta_memory_storage, cache_storage=content_memory_storage, logger=logger)
    meta_storage = meta_memory_storage.dict_for_debug()
    assert len(requests_mock.calls) == len(images) * 2
    assert len(meta_storage) == len(images)
    assert len(cache_storage) == len(images)


def test_fetch_urls_single_redis_and_s3(images, logger, requests_mock, redis_storage, content_s3_storage):
    for url, obj in images.items():
        requests_mock.add(
            requests_mock.GET, url, body=obj['image']
        )

    url_dict = urls_per_domain(images.keys())

    fetch_urls_single(url_dict, meta_storage=redis_storage, cache_storage=content_s3_storage, logger=logger)

    assert len(requests_mock.calls) == len(images)
