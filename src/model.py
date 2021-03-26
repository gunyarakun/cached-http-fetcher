import requests
from typing import Optional
from dataclasses import dataclass

@dataclass(frozen=True)
class Meta:
    external_url: str
    fetched_at: int
    expired_at: int


@dataclass(frozen=True)
class FetchedResponse:
    url: str
    fetched_at: int
    expired_at: int
    content_type: Optional[str]
    response: requests.Request
