import json
import multiprocessing
from dataclasses import dataclass
from typing import Dict, Set, Iterable, Optional

from storage import StorageBase
from request import requests_get, RequestException

@dataclass(frozen=True)
class FetchedImage:
    url: str
    image: bytes


class FetchWorker(multiprocessing.Process):
    def __init__(self, url_queue, image_queue, meta_storage):
        super().__init__()
        self._url_queue = url_queue
        self._image_queue = image_queue
        self._meta_storage = meta_storage
        self._logger = multiprocessing.get_logger()


    def run(self):
        while True:
            url_set = self._url_queue.get()
            if url_set is None:
                break

            for url in url_set:
                try:
                    response = requests_get(url, self._meta_storage)
                    self._image_queue.put(FetchedImage(url=url, image=response.content))
                except RequestException as e:
                    self._logger.warning(str(e))
                except Exception as e:
                    self._logger.warning(str(e))


class OptimizeWorker(multiprocessing.Process):
    def __init__(self, image_queue, meta_storage, image_storage):
        super().__init__()
        self._image_queue = image_queue
        self._meta_storage = meta_storage
        self._image_storage = image_storage
        self._logger = multiprocessing.get_logger()


    def run(self):
        while True:
            fetched_image = self._image_queue.get()
            if fetched_image is None:
                break

            # TODO: Optimize the image
            optimized_image = fetched_image.image

            # Save the image
            key_in_image_storage = fetched_image.url # FIXME: calc key from url
            self._image_storage.put(key_in_image_storage, optimized_image)

            # Save the meta info
            url_for_saved_image = self._image_storage.url_from_key(key_in_image_storage)
            self._meta_storage.put(fetched_image.url, json.dumps({
                "source": fetched_image.url,
                "optimized": url_for_saved_image,
                # TODO: Add some meta info for checking cache is valid or not
            }))


def url_queue_from_dict(url_dict: Dict[str, Set[str]]) -> multiprocessing.Queue:
    url_queue = multiprocessing.Queue()
    url_count = 0
    for domain, url_set in url_dict.items():
        url_queue.put(url_set)
        url_count += len(url_set)
    return url_queue


def fetch_images_single(url_dict: Dict[str, Set[str]], *, meta_storage: StorageBase, image_storage: StorageBase, logger):
    '''
        For testing, single process
    '''
    url_queue = url_queue_from_dict(url_dict)
    image_queue = multiprocessing.Queue()

    url_queue.put(None)
    fw = FetchWorker(url_queue, image_queue, meta_storage)
    fw.run()
    fw.close()
    image_queue.put(None)
    ow = OptimizeWorker(image_queue, meta_storage, image_storage)
    ow.run()
    ow.close()


def fetch_images(url_dict: Dict[str, Set[str]], *, meta_storage: StorageBase, image_storage: StorageBase, num_fetcher: Optional[int] = None, num_optimizer: Optional[int] = None, logger):
    fetch_jobs = []
    optimize_jobs = []
    url_queue = url_queue_from_dict(url_dict)
    image_queue = multiprocessing.Queue()

    num_fetcher = num_fetcher or multiprocessing.cpu_count() * 4
    num_optimizer = num_optimizer or multiprocessing.cpu_count()

    for i in range(num_fetcher):
        p = FetchWorker(url_queue, image_queue, meta_storage)
        fetch_jobs.append(p)
        p.start()

    for i in range(num_optimizer):
        p = OptimizeWorker(image_queue, meta_storage, image_storage)
        optimize_jobs.append(p)
        p.start()

    for j in fetch_jobs:
        url_queue.put(None)

    # Wait for fetching all the images
    for j in fetch_jobs:
        j.join()

    # Now nobody puts an item into `image_queue`, so we adds a terminator.
    for j in optimize_jobs:
        image_queue.put(None)

    # Wait for optimizing all the images
    for j in optimize_jobs:
        j.join()
