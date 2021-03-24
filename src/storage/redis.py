from .base import StorageBase

class RedisStorage(StorageBase):
    def __init__(self, *, redis_client):
        self.client = redis_client

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
