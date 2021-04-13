import hashlib
import random
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


def max_age_with_jitter(min_cache_age: int, max_age: int):
    if max_age < min_cache_age:
        # min_cache_age with jitter
        return min_cache_age + random.randint(0, min_cache_age)
    else:
        # min_cache_age <= max_age <= max_age
        return random.randint(min_cache_age, max_age)


def calc_expired_at(
    response_headers: CaseInsensitiveDict, now: int, min_cache_age: int
) -> int:
    try:
        cache_control = parse_cache_control(response_headers.get("cache-control", ""))

        if "no-store" in cache_control:
            return now + max_age_with_jitter(min_cache_age, 0)
        if "max-age" in cache_control:
            return now + max_age_with_jitter(
                min_cache_age, int(cache_control["max-age"])
            )
        if "expires" in response_headers:
            # TODO: check date header to get the base date
            expires = mktime_tz(parsedate_tz(response_headers["expires"]))
            return now + max_age_with_jitter(min_cache_age, expires - now)
    except Exception:
        pass
    return now + min_cache_age


def put_content(
    response: Response,
    old_meta: Optional[Meta],
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
            content = response.content or b""
            content_sha1 = hashlib.sha1(content).digest()

            if old_meta is None or old_meta.content_sha1 != content_sha1:
                content_type = response_headers.get("content-type", None)
                content_storage.put_content(
                    source_url,
                    content,
                    content_type=content_type,
                    cache_control=f"max-age={content_max_age}",
                )
        else:
            if old_meta is None:
                raise ValueError("old meta must be set on 304")
            content_sha1 = old_meta.content_sha1

        expired_at = calc_expired_at(response_headers, fetched_at, min_cache_age)

        return Meta(
            cached_url=cached_url,
            etag=response_headers.get("etag", None),
            last_modified=response_headers.get("last-modified", None),
            content_sha1=content_sha1,
            fetched_at=fetched_at,
            expired_at=expired_at,
        )
    # meta for non cacheable content
    return Meta(
        cached_url=None,
        etag=None,
        last_modified=None,
        content_sha1=None,
        fetched_at=fetched_at,
        expired_at=fetched_at + min_cache_age,
    )
