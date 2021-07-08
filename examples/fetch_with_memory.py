import argparse
import logging
from dataclasses import dataclass
from multiprocessing import Manager
from multiprocessing.managers import DictProxy  # type: ignore
from typing import Dict, Iterable, Optional

import cached_http_fetcher


class MemoryStorage(cached_http_fetcher.MetaStorageBase):
    def __init__(self, managed_dict: DictProxy) -> None:
        self.dict: Dict[str, bytes] = managed_dict

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


class ContentMemoryStorage(cached_http_fetcher.ContentStorageBase):
    def __init__(self, managed_dict: DictProxy) -> None:
        self.dict: Dict[str, ContentMemoryEntry] = managed_dict

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


def main(url_list: Iterable[str]) -> None:
    with Manager() as manager:
        meta_storage = MemoryStorage(manager.dict())  # type: ignore
        content_storage = ContentMemoryStorage(manager.dict())  # type: ignore
        logger = logging.getLogger(__name__)

        cached_http_fetcher.fetch_urls(
            url_list, meta_storage, content_storage, logger=logger
        )

        for url in url_list:
            meta = cached_http_fetcher.get_meta(url, meta_storage, logger=logger)
            if meta is not None:
                print(meta)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "url_list_file", help="url list to be fetched separated by line"
    )
    args = parser.parse_args()
    with open(args.url_list_file, "r") as f:
        url_list = f.read().splitlines()

    main(url_list)
