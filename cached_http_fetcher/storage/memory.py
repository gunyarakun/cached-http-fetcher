from typing import Optional
from .base import StorageBase, ContentStorageBase

class MemoryStorage(StorageBase):
    def __init__(self, **kwargs):
        self.dict = {}

    def get(self, key: str) -> Optional[bytes]:
        return self.dict.get(key, None)

    def put(self, key: str, value: bytes) -> None:
        if type(value) != bytes:
            raise ValueError
        self.dict[key] = value

    def delete(self, key: str) -> None:
        del self.dict[key]

    def dict_for_debug(self) -> dict:
        return self.dict

class ContentMemoryStorage(ContentStorageBase):
    def __init__(self, **kwargs):
        self.dict = {}

    def get(self, key: str) -> Optional[bytes]:
        v = self.dict.get(key, None)
        if v is not None:
            return v["value"]
        return None

    def delete(self, key: str) -> None:
        del self.dict[key]

    def put_content(self, key: str, value: bytes, content_type: Optional[str] = None, expire: Optional[int] = None) -> None:
        self.dict[key] = {
            "value": value,
            "content_type": content_type,
            "expire": expire,
        }

    def url_from_key(self, key: str) -> str:
        return f'memory:{key}'

    def dict_for_debug(self) -> dict:
        return self.dict
