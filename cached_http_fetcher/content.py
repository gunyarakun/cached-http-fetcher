from email.utils import mktime_tz, parsedate_tz
from typing import Dict, Optional

from requests import Response
from requests.structures import CaseInsensitiveDict

from .model import Meta
from .storage import ContentStorageBase


def parse_cache_control(cache_control: str) -> Dict[str, Optional[str]]:
    directives: Dict[str, Optional[str]] = {}

    for part in cache_control.split(","):
        part = part.strip()
        if not part:
            continue

        s = part.split("=", 1)
        key = s[0].strip()
        if len(s) == 2:
            directives[key] = s[1].strip()
        else:
            directives[key] = None

    return directives


def calc_expired_at(
    response_headers: CaseInsensitiveDict, now: int, min_cache_age: int
) -> int:
    try:
        cache_control = parse_cache_control(response_headers.get("cache-control", ""))

        if "no-store" in cache_control:
            return now + min_cache_age
        if "max-age" in cache_control:
            return now + max(min_cache_age, int(cache_control["max-age"]))
        if "expires" in response_headers:
            expires = mktime_tz(parsedate_tz(response_headers["expires"]))
            return now + max(expires - now, min_cache_age)
    except Exception:
        pass
    return now + min_cache_age


def put_content(
    response: Response,
    fetched_at: int,
    min_cache_age: int,
    content_max_age: int,
    content_storage: ContentStorageBase,
) -> Meta:
    source_url = response.url
    cached_url = content_storage.cached_url(source_url)

    # TODO: Improve handling 304
    if response.status_code == 200 or response.status_code == 304:
        response_headers = CaseInsensitiveDict(response.headers)

        if response.status_code == 200:
            content_type = response_headers.get("content-type", None)
            content_storage.put_content(
                source_url,
                response.content,
                content_type=content_type,
                cache_control=f"max-age={content_max_age}",
            )

        expired_at = calc_expired_at(response_headers, fetched_at, min_cache_age)

        return Meta(
            cached_url=cached_url,
            etag=response_headers.get("etag", None),
            last_modified=response_headers.get("last-modified", None),
            fetched_at=fetched_at,
            expired_at=expired_at,
        )
    # meta for non cacheable content
    return Meta(
        cached_url=None,
        etag=None,
        last_modified=None,
        fetched_at=fetched_at,
        expired_at=fetched_at + min_cache_age,
    )
