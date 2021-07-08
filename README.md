# Cached http fetcher

[![Test](https://github.com/gunyarakun/cached-http-fetcher/actions/workflows/test.yaml/badge.svg)](https://github.com/gunyarakun/cached-http-fetcher/actions/workflows/test.yaml)
[![PyPI version](https://badge.fury.io/py/cached-http-fetcher.svg)](https://badge.fury.io/py/cached-http-fetcher)

This library fetches data via HTTP(S), stores into some storages which is accessible from the internet.

## Install

```shell
pip install cached-http-fetcher
```

## Usage

The standard way to use this library is store metadata in Redis and store images itself in S3. The images in S3 can be accessed by the internet.

You have to implement your own meta storage extends `MetaStorageBase` with Redis and content storage extends `ContentStorageBase` with S3.

The whole sample code is following, or see and execute [fetch\_with\_memory.py](examples/fetch_with_memory.py).

```python
import boto3
from redis import Redis
import cached_http_fetcher
from urllib.parse import urlsplit, quote
from typing import Optional, Iterable
from botocore.exceptions import ClientError

import logging


class RedisMetaStorage(cached_http_fetcher.MetaStorageBase):
    def __init__(self, settings):
        self.redis = Redis.from_url("redis://redis:6379/0")

    def get(self, source_url: str) -> Optional[bytes]:
        return self.redis.get(source_url)

    def delete(self, source_url: str) -> None:
        self.redis.delete(source_url)

    def put(self, source_url: str, value: bytes) -> None:
        self.redis.set(source_url, value)


class S3ContentStorage(cached_http_fetcher.ContentStorageBase):
    def __init__(self, settings):
        self.s3 = boto3.client("s3")
        self.bucket = "some-bucket"

    @staticmethod
    def s3_key(source_url: str):
        r = urlsplit(source_url)
        s3_key = "path-prefix/"
        url = ''
        if r.scheme == "http":
            pass
        elif r.scheme == "https":
            s3_key += 's/'
        else:
            raise ValueError
        s3_key += r.netloc + r.path
        if r.query:
            s3_key += "?" + r.query
        return quote(s3_key)

    def get(self, source_url: str) -> bytes:
        try:
            obj = self.s3.get_object(Bucket=self.buclet, Key=S3ContentStorage.s3_key(source_url))
            return obj["Body"]
        except ClientError as ex:
            if ex.response["Error"]["Code"] == "NoSuchKey":
                return None
            else:
                raise

    def delete(self, source_url: str) -> None:
        self.client.delete_object(Bucket=self.bucket, Key=S3ContentStorage.s3_key(source_url))

    def put_content(self, source_url: str, value: bytes, cache_control: str, content_type: Optional[str] = None) -> None:
        config = dict(ACL="bucket-owner-full-control", Bucket=self.bucket, Key=key, CacheControl=cache_control, Body=value)
        if content_type:
            config["ContentType"] = content_type
        self.s3.put_object(**config)

    def cached_url(self, source_url: str) -> str:
        return f"https://{self.bucket}.s3.us-west-2.amazonaws.com/{S3ContentStorage.s3_key(source_url)}"


url_list = ["http://www.example.com/image1.jpg", "http://www.example.com/image2.jpg"]
meta_storage = RedisMetaStorage(settings)
content_storage = S3ContentStorage(settings)
logger = logging.getLogger(__name__)

cached_http_fetcher.fetch_urls(url_list, meta_storage, content_storage, logger=logger)

for url in url_list:
    meta = cached_http_fetcher.get_meta(url, meta_storage, logger=logger)
    print(meta.cached_url)
```

## Develop

```shell
make test # test
make dist # release to PyPI
```
