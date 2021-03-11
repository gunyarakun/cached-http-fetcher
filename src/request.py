from backoff import on_exception, expo
from requests.structures import CaseInsensitiveDict

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
