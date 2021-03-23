from typing import Dict, Set, Iterable
import requests
import multiprocessing
from dataclasses import dataclass

from storage import StorageBase
from request import requests_get

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
                    response = requests_get(url, meta_storage)
                    self._image_queue.put(FetchedImage(url=url, image=response.content))
                except requests.RequestException as e:
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
            url_for_saved_image = sel._image_storage.url_from_key(key_in_image_storage)
            meta_storage.put(fetched_image.url, {
                source: url,
                optimized: url_for_saved_image,
                # TODO: Add some meta info for checking cache is valid or not
            })


def fetch_images(url_dict: Dict[str, Set[str]], *, meta_storage: StorageBase, image_storage: StorageBase, logger):
    fetch_jobs = []
    optimize_jobs = []
    url_queue = multiprocessing.Queue()
    image_queue = multiprocessing.Queue()
    log_queue = multiprocessing.Queue()

    num_fetcher = multiprocessing.cpu_count() * 4
    num_fetcher = 1
    num_optimizer = multiprocessing.cpu_count()

    for i in range(num_fetcher):
        p = FetchWorker(url_queue, image_queue, meta_storage)
        fetch_jobs.append(p)
        p.start()

    for i in range(num_optimizer):
        p = OptimizeWorker(image_queue, meta_storage, image_storage)
        optimize_jobs.append(p)
        p.start()

    url_count = 0
    for domain, url_set in url_dict.items():
        url_queue.put(url_set)
        url_count += len(url_set)

    for j in fetch_jobs:
        url_queue.put(None)

    # Wait for fetching all the images
    for j in fetch_jobs:
        j.join()

    logger.info(f"Fetched all urls: {url_count}")

    # Now nobody puts an item into `image_queue`, so we adds a terminator.
    for j in optimize_jobs:
        image_queue.put(None)

    # Wait for optimizing all the images
    for j in optimize_jobs:
        j.join()
