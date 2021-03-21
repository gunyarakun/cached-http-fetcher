import pytest

from storage.memory import MemoryStorage

def test_memory_storage():
    memory_storage = MemoryStorage()

    memory_storage.put('key1', 'value1')
    memory_storage.put('key2', 'value2')
    assert memory_storage.get('key1') == 'value1'
    assert memory_storage.get('key2') == 'value2'
