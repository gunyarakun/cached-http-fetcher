from typing import Iterable

import io
import os
import sys
import pytest
import hashlib
from PIL import Image
import responses as responses_
from logging import getLogger, StreamHandler, DEBUG

from storage import StorageBase, ContentStorageBase

sys.path.append(os.path.abspath(os.path.dirname(os.path.abspath(__file__)) + "/../src/"))

IMAGES = {
    "http://domain1.example.com/image.jpg": {
        "width": 100,
        "height": 100,
        "format": "JPEG",
    },
    "https://domain1.example.com/image.jpg": {
        "width": 100,
        "height": 100,
        "format": "JPEG",
    },
    "https://domain1.example.com/large_image.jpg": {
        "width": 2000,
        "height": 2000,
        "format": "JPEG",
    },
    "https://domain1.example.com/path/image.jpg": {
        "width": 100,
        "height": 100,
        "format": "JPEG",
    },
    "https://domain2.example.com/image.jpg": {
        "width": 100,
        "height": 100,
        "format": "JPEG",
    },
    "https://domain3.example.com/image.jpg": {
        "width": 100,
        "height": 100,
        "format": "JPEG",
    },
    "https://domain3.example.com/image2.jpg": {
        "width": 100,
        "height": 100,
        "format": "JPEG",
    },
    "https://domain3.example.com/image3.jpg": {
        "width": 100,
        "height": 100,
        "format": "JPEG",
    },
    "https://domain3.example.com/image4.jpg": {
        "width": 100,
        "height": 100,
        "format": "JPEG",
    },
}

# create images
for url, obj in IMAGES.items():
    # generate color from url
    color = int(hashlib.sha256(url.encode('utf-8')).hexdigest(), 16) % 0xffffff

    img = Image.new("RGB", (obj["width"], obj["height"]), color=color)
    with io.BytesIO() as output:
        img.save(output, format=obj["format"])
        obj["image"] = output.getvalue()


@pytest.fixture(scope="session", autouse=True)
def url_list() -> Iterable[str]:
    return IMAGES.keys()


# TODO: type hint
@pytest.fixture(scope="session", autouse=True)
def images():
    return IMAGES


@pytest.fixture(scope="session", autouse=True)
def logger() -> Iterable[str]:
    l = getLogger(__name__)
    handler = StreamHandler()
    handler.setLevel(DEBUG)
    l.setLevel(DEBUG)
    l.addHandler(handler)
    l.propagate = False

    return l


@pytest.fixture(scope="function")
def requests_mock():
    with responses_.RequestsMock() as r:
        yield r


import time
import boto3
import fakeredis
from moto import mock_s3
from typing import Optional


class RedisStorage(StorageBase):
    def __init__(self, **kwargs):
        self.client = fakeredis.FakeStrictRedis()

    def get(self, key: str) -> bytes:
        v = self.client.get(key)
        if v is not None:
            return v["value"]

    def put(self, key: str, value: bytes) -> None:
        self.dict[key] = {
            "value": value,
        }

    def delete(self, key: str) -> None:
        del self.dict[key]

class ContentS3Storage(ContentStorageBase):
    def __init__(self, **kwargs):
        self.bucket = "content-memory-test"
        self.client = boto3.client("s3", region_name="us-east-1")
        self.client.create_bucket(Bucket=self.bucket)

    def get(self, key: str) -> bytes:
        try:
            obj = self.client.get_object(Bucket=self.bucket, Key=key)
            return obj["Body"]
        except ClientError as ex:
            if ex.response["Error"]["Code"] == "NoSuchKey":
                return None
            else:
                raise

    def put(self, key: str, value: bytes) -> None:
        config = dict(Bucket=self.bucket, Key=key, Body=value)
        return self.client.put_object(**config)

    def delete(self, key: str) -> None:
        raise NotImplementedError

    def put_content(self, key: str, value: bytes, content_type: Optional[str] = None, expire: Optional[int] = None) -> None:
        config = dict(Bucket=self.bucket, Key=key, Body=value)
        if content_type is not None:
            config['ContentType'] = content_type
        if expire is not None:
            max_age = expire - time.time()
            if max_age >= 0:
                config['CacheControl'] = f"max-age={max_age}"
        return self.client.put_object(**config)

    def url_from_key(self, key: str) -> str:
        return f'memory:{key}'


@pytest.fixture(scope="function")
def redis_storage():
    return RedisStorage()


@pytest.fixture(scope="function")
def content_s3_storage():
    with mock_s3():
        yield ContentS3Storage()
