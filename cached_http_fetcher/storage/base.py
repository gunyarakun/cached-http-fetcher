from typing import Optional
from abc import ABC, abstractmethod

class StorageBase(ABC):
    @abstractmethod
    def get(self, source_url: str) -> Optional[bytes]:
        pass

    @abstractmethod
    def delete(self, source_url: str) -> None:
        pass

    @abstractmethod
    def put(self, source_url: str, value: bytes) -> None:
        pass


class ContentStorageBase(ABC):
    @abstractmethod
    def get(self, key: str) -> Optional[bytes]:
        pass

    @abstractmethod
    def delete(self, key: str) -> None:
        pass

    @abstractmethod
    def put_content(self, key: str, value: bytes, content_type: Optional[str] = None, expire: Optional[int] = None) -> None:
        pass

    @abstractmethod
    def url_from_key(self, key: str) -> str:
        pass
