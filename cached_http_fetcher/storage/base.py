from typing import Optional
from abc import ABC, abstractmethod

class StorageBase(ABC):
    @abstractmethod
    def get(self, key: str) -> Optional[bytes]:
        pass

    @abstractmethod
    def put(self, key: str, value: bytes) -> None:
        pass

    @abstractmethod
    def delete(self, key: str) -> None:
        pass


class ContentStorageBase(StorageBase):
    @abstractmethod
    def put_content(self, key: str, value: bytes, content_type: Optional[str] = None, expire: Optional[int] = None) -> None:
        pass

    @abstractmethod
    def url_from_key(self, key: str) -> str:
        pass
