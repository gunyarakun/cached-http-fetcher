from dataclasses import dataclass
from typing import Optional

import requests


@dataclass(frozen=True)
class Meta:
    cached_url: Optional[str]  # None for non 200 responses
    etag: Optional[str]
    last_modified: Optional[str]
    fetched_at: int
    expired_at: int


@dataclass(frozen=True)
class FetchedResponse:
    url: str
    fetched_at: int
    response: requests.Request
