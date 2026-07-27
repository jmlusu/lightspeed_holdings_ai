from lightspeed_agents.memory.filestore import FileStore
from lightspeed_agents.memory.models import MemoryEntry


def test_filestore_save_and_load(tmp_path):
    store = FileStore(str(tmp_path))
    entries = [MemoryEntry(content="hello"), MemoryEntry(content="world")]
    store.save("test.json", entries)

    loaded = store.load("test.json")
    assert len(loaded) == 2
    assert loaded[0].content == "hello"
    assert loaded[1].content == "world"


def test_filestore_load_missing(tmp_path):
    store = FileStore(str(tmp_path))
    assert store.load("nonexistent.json") == []


def test_filestore_exists(tmp_path):
    store = FileStore(str(tmp_path))
    assert store.exists("test.json") is False
    store.save("test.json", [MemoryEntry(content="x")])
    assert store.exists("test.json") is True


def test_filestore_delete(tmp_path):
    store = FileStore(str(tmp_path))
    store.save("test.json", [MemoryEntry(content="x")])
    store.delete("test.json")
    assert store.exists("test.json") is False


def test_filestore_atomic_write(tmp_path):
    store = FileStore(str(tmp_path))
    store.save("test.json", [MemoryEntry(content="v1")])
    store.save("test.json", [MemoryEntry(content="v2")])

    loaded = store.load("test.json")
    assert len(loaded) == 1
    assert loaded[0].content == "v2"

    tmp_files = list(tmp_path.glob("*.tmp"))
    assert len(tmp_files) == 0
