import requests
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
    response: requests.Request
