from typing import Dict, Set, Iterable
import warnings
import requests
import multiprocessing
from dataclasses import dataclass
from ratelimit import limits, RateLimitException
from backoff import on_exception, expo

from requests.packages.urllib3.exceptions import InsecureRequestWarning
warnings.simplefilter("ignore", UserWarning)
warnings.simplefilter("ignore", InsecureRequestWarning)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.192 Safari/537.36",
}

@dataclass(frozen=True)
class FetchedImage:
    url: str
    image: bytes



@on_exception(expo, RateLimitException, max_tries=8)
@limits(calls=10, period=60) # 10 requests per 1 minute
def requests_get(url):
    response = requests.get(
        url,
        headers=HEADERS, verify=False, allow_redirects=True, stream=True, timeout=10)
    if response.status_code != 200:
        raise Exception(f"{response.status_code}: {url}")
    return response


class FetchWorker(multiprocessing.Process):
    def __init__(self, url_queue, image_queue):
        super().__init__()
        self._url_queue = url_queue
        self._image_queue = image_queue
        self._logger = multiprocessing.get_logger()


    def run(self):
        while True:
            url_set = self._url_queue.get()
            if url_set is None:
                break

            for url in url_set:
                try:
                    response = requests_get(url)
                    self._image_queue.put(FetchedImage(url=url, image=response.content))
                except requests.RequestException as e:
                    self._logger.warning(str(e))
                except Exception as e:
                    self._logger.warning(str(e))


class OptimizeWorker(multiprocessing.Process):
    def __init__(self, image_queue):
        super().__init__()
        self._image_queue = image_queue
        self._logger = multiprocessing.get_logger()


    def run(self):
        while True:
            fetched_image = self._image_queue.get()
            if fetched_image is None:
                break

            print(f"optimize: {fetched_image.url}")
            self._logger.info(f"optimize: {fetched_image.url}")


def fetch_images(url_dict: Dict[str, Set[str]], *, logger):
    fetch_jobs = []
    optimize_jobs = []
    url_queue = multiprocessing.Queue()
    image_queue = multiprocessing.Queue()
    log_queue = multiprocessing.Queue()

    num_fetcher = multiprocessing.cpu_count() * 4
    num_fetcher = 1
    num_optimizer = multiprocessing.cpu_count()

    for i in range(num_fetcher):
        p = FetchWorker(url_queue, image_queue)
        fetch_jobs.append(p)
        p.start()

    for i in range(num_optimizer):
        p = OptimizeWorker(image_queue)
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
