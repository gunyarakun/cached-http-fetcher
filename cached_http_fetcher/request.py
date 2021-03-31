from typing import Optional
import time
import requests
from requests import RequestException
from requests.structures import CaseInsensitiveDict # For headers
from backoff import on_exception, expo

from .storage import StorageBase
from .model import FetchedResponse
from .meta import get_meta

# Ignore some warnings
import warnings
from requests.packages.urllib3.exceptions import InsecureRequestWarning
warnings.simplefilter("ignore", UserWarning)
warnings.simplefilter("ignore", InsecureRequestWarning)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.192 Safari/537.36",
}


@on_exception(expo,
              (requests.exceptions.Timeout,
               requests.exceptions.ConnectionError),
              max_tries=4)
def requests_get(url: str):
    response = requests.get(
        url,
        headers=HEADERS, verify=False, allow_redirects=True, stream=True, timeout=10)
    return response


def cached_requests_get(url: str, meta_storage: StorageBase) -> Optional[requests.Request]:
    meta = get_meta(url, meta_storage)

    # already cached, so don't request
    if meta is not None:
        return None

    response = requests_get(url)
    response_headers = CaseInsensitiveDict(response.headers)

    now = time.time()
    # FIXME: calculate expired_at
    if response.status_code != 200:
        expired_at = now + 3600 # 1 hour for non 200
    else:
        expired_at = now + 60 * 60 * 24
    content_type = response_headers.get('content-type', None)

    return FetchedResponse(
        url=url,
        fetched_at=now,
        expired_at=expired_at,
        content_type=content_type,
        response=response,
    )
