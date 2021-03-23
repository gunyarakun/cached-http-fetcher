import pytest

from url_list import urls_per_domain
from fetcher import fetch_images
from storage import MemoryStorage

def test_fetch_images(url_list, logger):
    assert len(url_list) == 8
    url_dict = urls_per_domain(url_list)

    meta_memory_storage = MemoryStorage()
    image_memory_storage = MemoryStorage()

    fetch_images(url_dict, meta_storage=meta_memory_storage, image_storage=image_memory_storage, logger=logger)
