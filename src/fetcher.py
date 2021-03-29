import json
import pickle
import multiprocessing
from typing import Dict, Set, Iterable, Optional

from .model import Meta
from .url_list import urls_per_domain
from .storage import StorageBase, ContentStorageBase
from .request import cached_requests_get, RequestException

class FetchWorker(multiprocessing.Process):
    def __init__(self, url_queue, response_queue, meta_storage):
        super().__init__()
        self._url_queue = url_queue
        self._response_queue = response_queue
        self._meta_storage = meta_storage
        self._logger = multiprocessing.get_logger()


    def run(self):
        while True:
            url_set = self._url_queue.get()
            if url_set is None:
                break

            for url in url_set:
                try:
                    # FIXME: rate limit
                    fetched_response = cached_requests_get(url, self._meta_storage)
                    # fetched_response can be None when we don't need to fetch the cache
                    if fetched_response is not None:
                        self._response_queue.put(fetched_response)
                except RequestException as e:
                    self._logger.warning(str(e))
                except Exception as e:
                    self._logger.warning(str(e))


class OptimizeWorker(multiprocessing.Process):
    def __init__(self, response_queue, meta_storage, cache_storage):
        super().__init__()
        self._response_queue = response_queue
        self._meta_storage = meta_storage
        self._cache_storage = cache_storage
        self._logger = multiprocessing.get_logger()


    def run(self):
        while True:
            fetched_response = self._response_queue.get()
            if fetched_response is None:
                break

            # TODO: Apply filters to the cache
            filtered_response = fetched_response.response

            # Save response content into the cache
            key_in_cache_storage = fetched_response.url
            self._cache_storage.put_content(key_in_cache_storage, filtered_response.content,
                content_type=fetched_response.content_type, expire=fetched_response.expired_at)

            # Save the meta info
            url_for_saved_cache = self._cache_storage.url_from_key(key_in_cache_storage)
            meta = Meta(
                external_url=url_for_saved_cache,
                fetched_at=fetched_response.fetched_at,
                expired_at=fetched_response.expired_at,
            )
            self._meta_storage.put(fetched_response.url, pickle.dumps(meta))


def url_queue_from_list(url_list: Iterable[str]) -> multiprocessing.Queue:
    url_dict = urls_per_domain(url_list)
    url_queue = multiprocessing.Queue()
    url_count = 0
    for _domain, url_set in url_dict.items():
        url_queue.put(url_set)
        url_count += len(url_set)
    return url_queue


def fetch_urls_single(url_list: Iterable[str], *, meta_storage: StorageBase, cache_storage: ContentStorageBase, logger):
    '''
        For testing, single process
    '''
    url_queue = url_queue_from_list(url_list)
    response_queue = multiprocessing.Queue()

    url_queue.put(None)
    fw = FetchWorker(url_queue, response_queue, meta_storage)
    fw.run()
    fw.close()
    response_queue.put(None)
    ow = OptimizeWorker(response_queue, meta_storage, cache_storage)
    ow.run()
    ow.close()


def fetch_urls(url_list: Iterable[str], *, meta_storage: StorageBase, cache_storage: StorageBase, num_fetcher: Optional[int] = None, num_optimizer: Optional[int] = None, logger):
    fetch_jobs = []
    optimize_jobs = []
    url_queue = url_queue_from_list(url_list)
    response_queue = multiprocessing.Queue()

    num_fetcher = num_fetcher or multiprocessing.cpu_count() * 4
    num_optimizer = num_optimizer or multiprocessing.cpu_count()

    for _ in range(num_fetcher):
        p = FetchWorker(url_queue, response_queue, meta_storage)
        fetch_jobs.append(p)
        p.start()

    for _ in range(num_optimizer):
        p = OptimizeWorker(response_queue, meta_storage, cache_storage)
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
