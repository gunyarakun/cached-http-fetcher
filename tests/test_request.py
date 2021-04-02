from cached_http_fetcher.storage import MemoryStorage
from cached_http_fetcher.request import requests_get, cached_requests_get

def test_cached_requests_get(requests_mock):
    url = "https://example.com/image1.txt"
    requests_mock.add(
        requests_mock.GET, url, body=b"test"
    )

    meta_storage = MemoryStorage()
    meta_storage_dict = meta_storage.dict_for_debug()

    # First fetch
    fetched_response = cached_requests_get(url, meta_storage)

    assert fetched_response is not None
    assert len(meta_storage_dict) == 0
    assert fetched_response.url == url
    # TODO: Use freezegun to test
    # assert fetched_response.fetched_at == url
    assert fetched_response.response.status_code == 200
    assert fetched_response.response.content == b"test"
