import multiprocessing
import time
from logging import Logger
from typing import Iterable, Optional

from .content import put_content
from .meta import get_meta, put_meta
from .rate_limit_fetcher import RateLimitFetcher
from .storage import ContentStorageBase, MetaStorageBase
from .url_list import urls_per_domain

SHORT_CACHE_SECONDS = 3600
CONTENT_MAX_AGE = 3600


class FetchWorker(multiprocessing.Process):
    def __init__(
        self,
        url_queue,
        response_queue,
        meta_storage,
        max_fetch_count,
        fetch_count_window,
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

    def run(self):
        while True:
            url_set = self._url_queue.get()
            if url_set is None:
                break

            for url in url_set:
                now = int(time.time())
                meta = get_meta(url, now, self._meta_storage, logger=self._logger)
                for fetched_response in self._rate_limit_fetcher.fetch(url, meta, now):
                    self._response_queue.put(fetched_response)


class OptimizeWorker(multiprocessing.Process):
    def __init__(self, response_queue, meta_storage, content_storage):
        super().__init__()
        self._response_queue = response_queue
        self._meta_storage = meta_storage
        self._content_storage = content_storage
        self._logger = multiprocessing.get_logger()

    def run(self):
        while True:
            fetched_response = self._response_queue.get()
            if fetched_response is None:
                break

            # TODO: Apply filters to the cache
            filtered_response = fetched_response.response

            meta = put_content(
                filtered_response,
                fetched_response.fetched_at,
                SHORT_CACHE_SECONDS,
                CONTENT_MAX_AGE,
                self._content_storage,
            )
            put_meta(filtered_response.url, meta, self._meta_storage)


def url_queue_from_iterable(
    url_list: Iterable[str], logger: Logger
) -> multiprocessing.Queue:
    url_dict = urls_per_domain(url_list)
    url_queue = multiprocessing.Queue()
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
    logger: Logger,
) -> None:
    """
    A single process version of fetch_urls()
    """
    url_queue = url_queue_from_iterable(url_list, logger)
    response_queue = multiprocessing.Queue()

    url_queue.put(None)
    fw = FetchWorker(
        url_queue, response_queue, meta_storage, max_fetch_count, fetch_count_window
    )

    fw.run()
    fw.close()
    response_queue.put(None)
    ow = OptimizeWorker(response_queue, meta_storage, content_storage)
    ow.run()
    ow.close()
    logger.info(f"fetched")


def fetch_urls(
    url_list: Iterable[str],
    meta_storage: MetaStorageBase,
    content_storage: ContentStorageBase,
    *,
    max_fetch_count: int = 0,
    fetch_count_window: int = 0,
    num_fetcher: Optional[int] = None,
    num_processor: Optional[int] = None,
    logger: Logger,
) -> None:
    """
    Fetch urls, store meta data into meta_storage and store cached response body to content_storage

    :param url_list: List of urls to be fetched
    :param meta_storage: A storage for meta data, implements MetaStorageBase
    :param content_storage: A storage for response contents, implements ContentStorageBase
    :param max_fetch_count: A max fetch count in fetch_count_window for rate limit. When 0, no rate limit.
    :param fetch_count_window: Seconds for counting fetch for rate limit. When 0, no rate limit.
    :param num_fetcher: A number of fetcher processes
    :param num_processor: A number of processer processes
    :param logger: Logger
    """
    fetch_jobs = []
    optimize_jobs = []
    url_queue = url_queue_from_iterable(url_list, logger)

    response_queue = multiprocessing.Queue()

    num_fetcher = num_fetcher or multiprocessing.cpu_count() * 4
    num_processor = num_processor or multiprocessing.cpu_count()

    for _ in range(num_fetcher):
        p = FetchWorker(
            url_queue, response_queue, meta_storage, max_fetch_count, fetch_count_window
        )
        fetch_jobs.append(p)
        p.start()

    for _ in range(num_processor):
        p = OptimizeWorker(response_queue, meta_storage, content_storage)
        optimize_jobs.append(p)
        p.start()

    for _ in fetch_jobs:
        url_queue.put(None)

    # Wait for fetching all the caches
    for j in fetch_jobs:
        j.join()

    # Now nobody puts an item into `response_queue`, so we adds a terminator.
    for _ in optimize_jobs:
        response_queue.put(None)

    # Wait for optimizing all the caches
    for j in optimize_jobs:
        j.join()

    logger.info(f"fetched")


def get_cached_url(
    url: str,
    meta_storage: MetaStorageBase,
    *,
    now: int = int(time.time()),
    logger: Logger,
) -> Optional[str]:
    """
    Fetch a cached url for the given url

    :param url: Source url
    :param now: Current epoch for cache validation. When 0, expired cached url is returned.
    :param meta_storage: A storage for meta data, implements MetaStorageBase
    :param logger: Logger
    """

    meta = get_meta(url, now, meta_storage, logger=logger)
    if meta is None:
        return None

    cached_url = meta.cached_url
    return cached_url
