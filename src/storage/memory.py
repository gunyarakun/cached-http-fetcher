from typing import Optional
from .base import StorageBase

class MemoryStorage(StorageBase):
    def __init__(self, **kwargs):
        self.dict = {}

    def get(self, key: str) -> bytes:
        v = self.dict.get(key, None)
        if v is not None:
            return v["value"]

    def put(self, key: str, value: bytes) -> None:
        self.dict[key] = {
            "value": value,
        }

    def put_for_external(self, key: str, value: bytes, content_type: str = None, expire: Optional[int] = None) -> None:
        self.dict[key] = {
            "value": value,
            "content_type": content_type,
            "expire": expire,
        }

    def delete(self, key: str) -> None:
        del self.dict[key]

    def url_from_key(self, key: str) -> str:
        return f'memory:{key}'

    def dict_for_debug(self) -> dict:
        return self.dict
