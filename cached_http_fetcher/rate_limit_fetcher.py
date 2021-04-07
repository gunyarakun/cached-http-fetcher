import sys
import time
from logging import Logger
from typing import Generator, Optional

from requests import RequestException

from .model import FetchedResponse, Meta
from .request import cached_requests_get


class RateLimitFetcher:
    def __init__(
        self, *, max_fetch_count: int, fetch_count_window: int, logger: Logger
    ):
        self._max_fetch_count = max_fetch_count
        self._fetch_count_window = fetch_count_window
        if self._max_fetch_count == 0 or self._fetch_count_window == 0:
            self._max_fetch_count = sys.maxsize
            self._fetch_count_window = sys.maxsize
        self._logger = logger

        self.fetch_count_start = time.time()
        self.fetch_count = 0

    def fetch(
        self, url: str, old_meta: Optional[Meta], now: int
    ) -> Generator[FetchedResponse, None, None]:
        try:
            elapsed = now - self.fetch_count_start
            remaining = self._fetch_count_window - elapsed
            if remaining <= 0:
                self.fetch_count_start = time.time()
                self.fetch_count = 0

            fetched_response = cached_requests_get(
                url, old_meta, now, logger=self._logger
            )

            # fetched_response can be None when we don't need to fetch the cache
            if fetched_response is not None:
                yield fetched_response

                self.fetch_count += 1
                if self.fetch_count > self._max_fetch_count:
                    time.sleep(remaining)
        except RequestException as e:
            self._logger.warning(str(e))
        except Exception as e:
            self._logger.warning(str(e))
