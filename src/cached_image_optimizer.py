import sys
from logging import getLogger, StreamHandler, DEBUG

from url_list import urls_per_domain
from fetcher import fetch_images

from .storage.redis import RedisStorage
from .storage.s3 import S3Storage
from .storage.memory import MemoryStorage

if __name__ == '__main__':
    logger = getLogger(__name__)
    handler = StreamHandler()
    handler.setLevel(DEBUG)
    logger.setLevel(DEBUG)
    logger.addHandler(handler)
    logger.propagate = False

    url_list = [x.strip() for x in sys.stdin.readlines()]
    logger.debug(url_list)
    url_dict = urls_per_domain(url_list)
    logger.debug(url_dict)
    #meta_redis_storage = RedisStorage()
    #image_s3_storage = S3Storage()
    meta_memory_storage = MemoryStorage()
    image_memory_storage = MemoryStorage()

    fetch_images(url_dict, meta_storage=meta_memory_storage, image_storage=image_memory_storage, logger=logger)
