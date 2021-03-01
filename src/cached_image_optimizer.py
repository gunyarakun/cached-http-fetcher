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
    response = requestsrequests.get(
        url.strip(),
        headers=HEADERS, verify=False, allow_redirects=True, stream=True, timeout=10)
    if response.status_code != 200:
        raise Exception(f"API response: {response.status_code}")
    return response


class Worker(multiprocessing.Process):
    def __init__(self, job_queue):
        super().__init__()
        self._job_queue = job_queue


    def run(self):
        while True:
            url = self._job_queue.get()
            if url is None:
                break

            try:
                response = requests_get(url)
            except requests.RequestException as e:
                pass


if __name__ == '__main__':
    jobs = []
    job_queue = multiprocessing.Queue()

    for i in range(5):
        p = Worker(job_queue)
        jobs.append(p)
        p.start()

    # This is the master code that feeds URLs into queue.
    with open('ips.txt', 'r') as urls:
        for url in urls.readlines():
            job_queue.put(url)

    # Send None for each worker to check and quit.
    for j in jobs:
        job_queue.put(None)

    for j in jobs:
        j.join()
