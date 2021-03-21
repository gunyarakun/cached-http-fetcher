from .base import StorageBase
from redis import Redis

class RedisStorage(StorageBase):
    def __init__(self, **kwargs):
        if "url" in kwargs:
            self.client = Redis.from_url(kwargs["url"])
        elif "host" in kwargs and "port" in kwargs and "db" in kwargs:
            self.client = Redis(**kwargs)
        else:
            raise ValueError

    def get(self, key: str) -> bytes:
        self.client.get(key)

    def put(self, key: str, value: bytes, expire=None) -> None:
        self.client.set(key, value, ex=expire)
        config = dict(ACL="bucket-owner-full-control", Bucket=self.bucket, Key=key, ContentType=content_type, Body=value)
        if expire:
            # FIXME: set proper expire
            config["CacheControl"] = expire
        return self.client.put_object(**config)

    def url_from_key(self, key: str) -> str:
        raise NotImplementedError
