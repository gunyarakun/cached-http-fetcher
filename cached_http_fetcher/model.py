import requests
from typing import Optional
from dataclasses import dataclass

@dataclass(frozen=True)
class Meta:
    cached_url: Optional[str] # None for non 200 responses
    fetched_at: int
    expired_at: int


@dataclass(frozen=True)
class FetchedResponse:
    url: str
    fetched_at: int
    expired_at: int
    content_type: Optional[str]
    response: requests.Request
