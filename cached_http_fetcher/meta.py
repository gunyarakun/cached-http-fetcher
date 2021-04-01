import time
import pickle
from typing import Optional

from .model import Meta
from .storage import StorageBase


def url_normalize(url: str) -> str:
    # FIXME: implement
    return url


def put_meta(url: str, meta_storage: StorageBase, *, cached_url: str, etag: Optional[str], last_modified: Optional[str], fetched_at: int, expired_at: Optional[int]):
    meta = Meta(
        cached_url=cached_url,
        etag=etag,
        last_modified=last_modified,
        fetched_at=fetched_at,
        expired_at=expired_at,
    )
    meta_storage.put(url, pickle.dumps(meta))


def get_meta(url: str, meta_storage: StorageBase) -> Meta:
    """
    get a valid Meta instance from url
    """

    norm_url = url_normalize(url)

    now = time.time()

    meta_pickled = meta_storage.get(norm_url)
    if meta_pickled is None:
        return None
    try:
        meta = pickle.loads(meta_pickled)
        if meta.expired_at < now:
            meta_storage.delete(norm_url)
            return None
        return meta
    except:
        meta_storage.delete(norm_url)
        raise
