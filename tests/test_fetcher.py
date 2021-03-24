import pytest

from url_list import urls_per_domain
from fetcher import fetch_images, fetch_images_single
from storage import MemoryStorage, S3Storage, RedisStorage


class S3Client:
    def __init__(self):
        self.dict = {}

    def get_object(self, **kwargs):
        return self.dict[kwargs["Key"]]

    def put_object(self, **kwargs):
        self.dict[kwargs["Key"]] = kwargs


class RedisClient:
    def __init__(self):
        self.dict = {}

    def get(self, key):
        return self.dict[key]

    def set(self, key, value, expire=None):
        self.dict[key] = value


def test_fetch_images_single_memory(images, logger, requests_mock):
    for url, obj in images.items():
        requests_mock.add(
            requests_mock.GET, url, body=obj['image']
        )

    url_dict = urls_per_domain(images.keys())

    # memory storage
    meta_memory_storage = MemoryStorage()
    image_memory_storage = MemoryStorage()

    fetch_images_single(url_dict, meta_storage=meta_memory_storage, image_storage=image_memory_storage, logger=logger)

    meta_storage = meta_memory_storage.dict_for_debug()
    image_storage = image_memory_storage.dict_for_debug()

    assert len(requests_mock.calls) == len(images)
    assert len(meta_storage) == len(images)
    assert len(image_storage) == len(images)

    # TODO: Add more tests


def test_fetch_images_redis_s3(images, logger, requests_mock):
    for url, obj in images.items():
        requests_mock.add(
            requests_mock.GET, url, body=obj['image']
        )

    url_dict = urls_per_domain(images.keys())

    # redis/s3 storage
    meta_redis_storage = RedisStorage(redis_client=RedisClient())
    image_s3_storage = S3Storage(bucket='test_bucket', boto3_s3_client=S3Client())

    fetch_images_single(url_dict, meta_storage=meta_redis_storage, image_storage=image_s3_storage, logger=logger)

    assert len(requests_mock.calls) == len(images)
