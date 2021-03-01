from cached_http_fetcher.storage.memory import MemoryStorage


def test_memory_storage():
    memory_storage = MemoryStorage()

    memory_storage.put("key1", b"value1")
    memory_storage.put("key2", b"value2")
    assert memory_storage.get("key1") == b"value1"
    assert memory_storage.get("key2") == b"value2"
