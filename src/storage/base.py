from abc import ABC

class StorageBase(ABC):
    @abstractmethod
    def get(self, key: str) -> bytes:
        pass

    @abstractmethod
    def put(self, key: str, value: bytes, expire=None) -> None:
        # expire in seconds
        pass
