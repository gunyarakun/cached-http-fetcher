from typing import Dict, Set, Iterable
import warnings
import requests
import multiprocessing
from ratelimit import limits, RateLimitException
from backoff import on_exception, expo

from requests.packages.urllib3.exceptions import InsecureRequestWarning
warnings.simplefilter("ignore", UserWarning)
warnings.simplefilter("ignore", InsecureRequestWarning)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.192 Safari/537.36",
}

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
    def __init__(self, job_queue, *, logger):
        super().__init__()
        self._job_queue = job_queue
        self._logger = logger


    def run(self):
        while True:
            url_set = self._job_queue.get()
            if url_set is None:
                break

            for url in url_set:
                try:
                    response = requests_get(url)
                except requests.RequestException as e:
                    self._logger.warning(str(e))
                except Exception as e:
                    self._logger.warning(str(e))


def fetch_images(url_dict: Dict[str, Set[str]], *, logger):
    jobs = []
    job_queue = multiprocessing.Queue()

    for i in range(16):
        p = FetchWorker(job_queue, logger=logger)
        jobs.append(p)
        p.start()

    for domain, url_set in url_dict.items():
        job_queue.put(url_set)

    for j in jobs:
        job_queue.put(None)

    for j in jobs:
        j.join()
