from typing import Optional
from requests import Response
from email.utils import parsedate_tz, mktime_tz
from requests.structures import CaseInsensitiveDict

from .model import ParsedHeader
from .storage import ContentStorageBase


def parse_cache_control(cache_control: str):
    directives = {}

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


def calc_expired_at(response_headers: CaseInsensitiveDict, now: int, min_cache_age: int) -> int:
    try:
        cache_control = parse_cache_control(response_headers.get("cache-control", ""))

        if "no-store" in cache_control:
            return now + min_cache_age
        if "max-age" in cache_control:
            return now + max(min_cache_age, int(cache_control["max-age"]))
        if "expires" in response_headers:
            expires = mktime_tz(parsedate_tz(response_headers["expires"]))
            return now + max(expires - now, min_cache_age)
    except:
        pass
    return now + min_cache_age


def put_content(source_url: str, response: Response, min_cache_age: int, content_max_age: int, now: int, content_storage: ContentStorageBase) -> Optional[ParsedHeader]:
    # TODO: Improve handling 304
    if response.status_code == 200 or response.status_code == 304:
        response_headers = CaseInsensitiveDict(response.headers)

        if response.status_code == 200:
            content_type = response_headers.get("content-type", None)
            content_storage.put_content(
                    source_url,
                    response.content,
                    content_type=content_type,
                    cache_control=f"max-age={content_max_age}"
            )

        expired_at = calc_expired_at(response_headers, now, min_cache_age)
        return ParsedHeader(
            etag=response_headers.get("etag", None),
            last_modified=response_headers.get("last_modified", None),
            expired_at=expired_at,
        )
    return None
