from .base import StorageBase

class MemoryStorage(StorageBase):
    def __init__(self, **kwargs):
        self.dict = {}

    def get(self, key: str) -> bytes:
        return self.dict.get(key, None)

    def put(self, key: str, value: bytes, expire=None) -> None:
        self.dict[key] = value

    def url_from_key(self, key: str) -> str:
        return f'memory:{key}'
