import pickle
from logging import Logger
from typing import Optional

from .model import Meta
from .storage import MetaStorageBase


def put_meta(
    source_url: str, meta: Optional[Meta], meta_storage: MetaStorageBase
) -> None:
    if meta is None:
        meta_storage.delete(source_url)
    else:
        meta_storage.put(source_url, pickle.dumps(meta))


def get_meta(
    source_url: str, meta_storage: MetaStorageBase, *, logger: Logger
) -> Optional[Meta]:
    """
    get a Meta instance from url
    """

    meta_pickled = meta_storage.get(source_url)
    if meta_pickled is None:
        return None
    try:
        meta: Meta = pickle.loads(meta_pickled)
        return meta
    except Exception:
        logger.error(f"Invalid meta data: {source_url}")
        # Remove invalid entry
        meta_storage.delete(source_url)
        raise


def get_valid_meta(
    source_url: str, now: int, meta_storage: MetaStorageBase, *, logger: Logger
) -> Optional[Meta]:
    """
    get a valid Meta instance from url

    :param now: current epoch for cache invalidation. When 0, no cache invalidation.
    """

    meta = get_meta(source_url, meta_storage, logger=logger)
    if meta is None or (now > 0 and meta.expired_at < now):
        return None
    return meta
