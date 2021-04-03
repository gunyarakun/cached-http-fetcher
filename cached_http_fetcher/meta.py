import pickle
from typing import Optional

from .model import Meta
from .storage import MetaStorageBase


def put_meta(source_url: str, meta: Meta, meta_storage: MetaStorageBase) -> None:
    meta_storage.put(source_url, pickle.dumps(meta))


def get_meta(
    url: str, now: int, meta_storage: MetaStorageBase, *, logger
) -> Optional[Meta]:
    """
    get a valid Meta instance from url

    :param now: current epoch for cache invalidation. When 0, no cache invalidation.
    """

    # TODO: Implement url normalizer
    norm_url = url

    meta_pickled = meta_storage.get(norm_url)
    if meta_pickled is None:
        return None
    try:
        meta: Meta = pickle.loads(meta_pickled)
        if now > 0 and meta.expired_at < now:
            logger.info(
                f"Invalidate meta data (expired_at={meta.expired_at}): {norm_url}"
            )
            meta_storage.delete(norm_url)
            # TODO: Remove content
            return None
        return meta
    except Exception:
        # Remove invalid entry
        logger.error(f"Invalid meta data: {norm_url}")
        raise
