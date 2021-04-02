from cached_http_fetcher.meta import get_meta, put_meta
from cached_http_fetcher.model import Meta
from cached_http_fetcher.storage import MemoryStorage


def test_get_meta():
    now = 1617355068
    future = now + 3600
    past = now - 3600
    url = "http://example.com/image1.jpg"
    cached_url = "http://cdn.example.com/example.com/image1.jpg"

    meta_storage = MemoryStorage()
    meta_storage_dict = meta_storage.dict_for_debug()

    # get empty
    meta = get_meta(url, now, meta_storage)
    assert meta is None

    # get non-expired meta
    meta = Meta(
        cached_url=cached_url,
        etag=None,
        last_modified=None,
        fetched_at=now,
        expired_at=future,
    )
    put_meta(url, meta, meta_storage)
    assert get_meta(url, now, meta_storage) == meta
    assert len(meta_storage_dict) == 1  # this entry will be deleted on the next call

    # get expired meta
    meta = Meta(
        cached_url=cached_url,
        etag=None,
        last_modified=None,
        fetched_at=now,
        expired_at=past,
    )
    put_meta(url, meta, meta_storage)
    assert get_meta(url, now, meta_storage) is None
    assert len(meta_storage_dict) == 0  # deleted
