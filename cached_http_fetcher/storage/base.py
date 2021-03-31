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
    def get(self, source_url: str) -> Optional[bytes]:
        pass

    @abstractmethod
    def delete(self, source_url: str) -> None:
        pass

    @abstractmethod
    def put_content(self, source_url: str, value: bytes, content_type: Optional[str] = None, expire: Optional[int] = None) -> None:
        pass

    @abstractmethod
    def cached_url(self, source_url: str) -> str:
        pass
