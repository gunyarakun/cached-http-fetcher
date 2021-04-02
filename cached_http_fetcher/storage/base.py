from abc import ABC, abstractmethod
from typing import Optional


class MetaStorageBase(ABC):
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
    def put_content(
        self,
        source_url: str,
        value: bytes,
        cache_control: str,
        content_type: Optional[str] = None,
    ) -> None:
        pass

    @abstractmethod
    def cached_url(self, source_url: str) -> str:
        pass
