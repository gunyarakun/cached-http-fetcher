from dataclasses import dataclass
from typing import Dict, Optional

from .base import ContentStorageBase, MetaStorageBase


class MemoryStorage(MetaStorageBase):
    def __init__(self) -> None:
        self.dict: Dict[str, bytes] = {}

    def get(self, source_url: str) -> Optional[bytes]:
        return self.dict.get(source_url, None)

    def put(self, source_url: str, value: bytes) -> None:
        if not isinstance(value, bytes):
            raise ValueError
        self.dict[source_url] = value

    def delete(self, source_url: str) -> None:
        del self.dict[source_url]

    def dict_for_debug(self) -> Dict[str, bytes]:
        return self.dict


@dataclass(frozen=True)
class ContentMemoryEntry:
    value: bytes
    cache_control: str
    content_type: Optional[str]


class ContentMemoryStorage(ContentStorageBase):
    def __init__(self) -> None:
        self.dict: Dict[str, ContentMemoryEntry] = {}

    def get(self, source_url: str) -> Optional[bytes]:
        v = self.dict.get(source_url, None)
        if v is not None:
            return v.value
        return None

    def delete(self, source_url: str) -> None:
        del self.dict[source_url]

    def put_content(
        self,
        source_url: str,
        value: bytes,
        cache_control: str,
        content_type: Optional[str] = None,
    ) -> None:
        self.dict[source_url] = ContentMemoryEntry(
            value=value,
            cache_control=cache_control,
            content_type=content_type,
        )

    def cached_url(self, source_url: str) -> str:
        return f"memory:{source_url}"

    def dict_for_debug(self) -> Dict[str, ContentMemoryEntry]:
        return self.dict
