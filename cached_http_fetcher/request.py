from typing import Optional
import time
import requests
from requests import RequestException
from backoff import on_exception, expo

from .model import FetchedResponse, Meta

# Ignore some warnings
import warnings
from requests.packages.urllib3.exceptions import InsecureRequestWarning
warnings.simplefilter("ignore", UserWarning)
warnings.simplefilter("ignore", InsecureRequestWarning)

USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.192 Safari/537.36"


@on_exception(expo,
              (requests.exceptions.Timeout,
               requests.exceptions.ConnectionError),
              max_tries=4)
def requests_get(url: str, headers: dict):
    headers["User-Agent"] = USER_AGENT
    response = requests.get(
        url,
        headers=headers, verify=False, allow_redirects=True, stream=True, timeout=10)
    return response


def cached_requests_get(url: str, meta: Optional[Meta], now: int) -> Optional[FetchedResponse]:
    req_headers = {}

    if meta is not None:
        if meta.expired_at > now:
            # already cached and valid, so don't request
            return None
        if meta.etag is not None:
            req_headers["If-None-Match"] = meta.etag
        if meta.last_modified is not None:
            req_headers["If-Modified-Since"] = meta.last_modified

    response = requests_get(url, req_headers)

    return FetchedResponse(
        url=url,
        fetched_at=now,
        response=response,
    )
