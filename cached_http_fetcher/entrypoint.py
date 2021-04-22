import multiprocessing
import time
from logging import Logger
from typing import Iterable, Optional, Set

from .content import put_content
from .meta import get_valid_meta, put_meta
from .model import FetchedResponse
from .rate_limit_fetcher import RateLimitFetcher
from .storage import ContentStorageBase, MetaStorageBase
from .url_list import urls_per_domain

DEFAULT_MIN_CACHE_AGE = 86400
DEFAULT_CONTENT_MAX_AGE = 3600


class FetchWorker(multiprocessing.Process):
    def __init__(
        self,
        url_queue: "multiprocessing.Queue[Optional[Set[str]]]",
        response_queue: "multiprocessing.Queue[Optional[FetchedResponse]]",
        meta_storage: MetaStorageBase,
        max_fetch_count: int,
        fetch_count_window: int,
    ):
        super().__init__()
        self._url_queue = url_queue
        self._response_queue = response_queue
        self._meta_storage = meta_storage
        self._logger = multiprocessing.get_logger()
        self._rate_limit_fetcher = RateLimitFetcher(
            max_fetch_count=max_fetch_count,
            fetch_count_window=fetch_count_window,
            logger=self._logger,
        )

    def run(self) -> None:
        while True:
            url_set = self._url_queue.get()
            if url_set is None:
                break

            for url in url_set:
                now = int(time.time())
                try:
                    old_meta = get_valid_meta(
                        url, now, self._meta_storage, logger=self._logger
                    )
                    for fetched_response in self._rate_limit_fetcher.fetch(
                        url, old_meta, now
                    ):
                        self._response_queue.put(fetched_response)
                except Exception as ex:
                    self._logger.exception("Error on FetchWorker: %s", ex)


class ContentWorker(multiprocessing.Process):
    def __init__(
        self,
        response_queue: "multiprocessing.Queue[Optional[FetchedResponse]]",
        min_cache_age: int,
        content_max_age: int,
        meta_storage: MetaStorageBase,
        content_storage: ContentStorageBase,
    ):
        super().__init__()
        self._response_queue = response_queue
        self._min_cache_age = min_cache_age
        self._content_max_age = content_max_age
        self._meta_storage = meta_storage
        self._content_storage = content_storage
        self._logger = multiprocessing.get_logger()

    def run(self) -> None:
        while True:
            fetched_response = self._response_queue.get()
            if fetched_response is None:
                break

            try:
                meta = put_content(
                    fetched_response,
                    self._min_cache_age,
                    self._content_max_age,
                    self._content_storage,
                    logger=self._logger,
                )
                put_meta(fetched_response.url, meta, self._meta_storage)
            except Exception as ex:
                self._logger.exception("Error on ContentWorker: %s", ex)


def url_queue_from_iterable(
    url_list: Iterable[str], logger: Logger
) -> "multiprocessing.Queue[Optional[Set[str]]]":
    url_dict = urls_per_domain(url_list)
    url_queue: "multiprocessing.Queue[Optional[Set[str]]]" = multiprocessing.Queue()
    domain_count = 0
    url_count = 0
    for _domain, url_set in url_dict.items():
        url_queue.put(url_set)
        domain_count += 1
        url_count += len(url_set)

    logger.info(f"fetch {url_count} urls from {domain_count} domains")

    return url_queue


def fetch_urls_single(
    url_list: Iterable[str],
    *,
    meta_storage: MetaStorageBase,
    content_storage: ContentStorageBase,
    max_fetch_count: int = 0,
    fetch_count_window: int = 0,
    min_cache_age: int = DEFAULT_MIN_CACHE_AGE,
    content_max_age: int = DEFAULT_CONTENT_MAX_AGE,
    logger: Logger,
) -> None:
    """
    A single process version of fetch_urls()
    """
    url_queue = url_queue_from_iterable(url_list, logger)
    response_queue: multiprocessing.Queue[
        Optional[FetchedResponse]
    ] = multiprocessing.Queue()

    url_queue.put(None)
    fw = FetchWorker(
        url_queue, response_queue, meta_storage, max_fetch_count, fetch_count_window
    )

    fw.run()
    fw.close()
    response_queue.put(None)
    ow = ContentWorker(
        response_queue, min_cache_age, content_max_age, meta_storage, content_storage
    )
    ow.run()
    ow.close()
    logger.info("fetched")


def fetch_urls(
    url_list: Iterable[str],
    meta_storage: MetaStorageBase,
    content_storage: ContentStorageBase,
    *,
    rate_limit_count: int = 0,
    rate_limit_seconds: int = 0,
    min_cache_age: int = DEFAULT_MIN_CACHE_AGE,
    content_max_age: int = DEFAULT_CONTENT_MAX_AGE,
    num_fetch_processes: Optional[int] = None,
    num_content_processes: Optional[int] = None,
    logger: Logger,
) -> None:
    """
    Fetch urls, store meta data into meta_storage and store cached response body to content_storage

    :param url_list: List of urls to be fetched
    :param meta_storage: A storage for meta data, implements MetaStorageBase
    :param content_storage: A storage for response contents, implements ContentStorageBase
    :param rate_limit_count: A max fetch count in fetch_count_window for rate limit. When 0, no rate limit.
    :param rate_limit_seconds: Seconds for counting fetch for rate limit. When 0, no rate limit.
    :param num_fetch_processes: A number of fetcher processes
    :param num_content_processes: A number of processer processes
    :param logger: Logger
    """
    fetch_jobs = []
    content_jobs = []
    url_queue = url_queue_from_iterable(url_list, logger)

    response_queue: multiprocessing.Queue[
        Optional[FetchedResponse]
    ] = multiprocessing.Queue()

    num_fetch_processes = num_fetch_processes or multiprocessing.cpu_count() * 4
    num_content_processes = num_content_processes or multiprocessing.cpu_count()

    for _ in range(num_fetch_processes):
        fw = FetchWorker(
            url_queue,
            response_queue,
            meta_storage,
            rate_limit_count,
            rate_limit_seconds,
        )
        fetch_jobs.append(fw)
        fw.start()

    for _ in range(num_content_processes):
        cw = ContentWorker(
            response_queue,
            min_cache_age,
            content_max_age,
            meta_storage,
            content_storage,
        )
        content_jobs.append(cw)
        cw.start()

    for _ in fetch_jobs:
        url_queue.put(None)

    # Wait for fetching all the caches
    for fj in fetch_jobs:
        fj.join()

    # Now nobody puts an item into `response_queue`, so we adds a terminator.
    for _ in content_jobs:
        response_queue.put(None)

    # Wait for optimizing all the caches
    for cj in content_jobs:
        cj.join()

    logger.info("fetched")
