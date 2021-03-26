from typing import Optional
import time
import requests
from requests import RequestException
from requests.structures import CaseInsensitiveDict # For headers
from backoff import on_exception, expo

from storage import StorageBase
from model import FetchedResponse

# Ignore some warnings
import warnings
from requests.packages.urllib3.exceptions import InsecureRequestWarning
warnings.simplefilter("ignore", UserWarning)
warnings.simplefilter("ignore", InsecureRequestWarning)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.192 Safari/537.36",
}


def url_normalize(url: str) -> str:
    # TODO: implement
    return url


@on_exception(expo,
              (requests.exceptions.Timeout,
               requests.exceptions.ConnectionError),
              max_tries=4)
def requests_get(url: str, meta_storage: StorageBase) -> Optional[requests.Request]:
    norm_url = url_normalize(url)

    now = time.time()

    meta = meta_storage.get(norm_url)
    if meta is not None:
        if meta.expired_at < now:
            meta_storege.delete(norm_url)
        else:
            # already cached
            return None

    response = requests.get(
        url,
        headers=HEADERS, verify=False, allow_redirects=True, stream=True, timeout=10)
    if response.status_code != 200:
        raise Exception(f"{response.status_code}: {url}")

    # FIXME: calculate expired_at
    expired_at = now + 60 * 60 * 24

    return FetchedResponse(
        url=url,
        fetched_at=now,
        expired_at=expired_at,
        response=response,
    )
