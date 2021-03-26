from typing import Optional
from abc import ABC, abstractmethod

class StorageBase(ABC):
    @abstractmethod
    def get(self, key: str) -> bytes:
        pass

    @abstractmethod
    def put(self, key: str, value: bytes) -> None:
        pass

    @abstractmethod
    def put_for_external(self, key: str, value: bytes, content_type: str = None, expire: Optional[int] = None) -> None:
        pass

    @abstractmethod
    def delete(self, key: str) -> None:
        pass

    @abstractmethod
    def url_from_key(self, key: str) -> str:
        pass
