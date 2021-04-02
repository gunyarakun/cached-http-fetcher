import pickle
from typing import Optional

from .model import Meta
from .storage import StorageBase


def put_meta(source_url: str, meta: Meta, meta_storage: StorageBase) -> None:
    meta_storage.put(source_url, pickle.dumps(meta))


def get_meta(url: str, now: int, meta_storage: StorageBase) -> Optional[Meta]:
    """
    get a valid Meta instance from url
    """

    # TODO: Implement url normalizer
    norm_url = url

    meta_pickled = meta_storage.get(norm_url)
    if meta_pickled is None:
        return None
    try:
        meta = pickle.loads(meta_pickled)
        if meta.expired_at < now:
            meta_storage.delete(norm_url)
            # TODO: Remove content
            return None
        return meta
    except:
        # Remove invalid entry
        meta_storage.delete(norm_url)
        raise
