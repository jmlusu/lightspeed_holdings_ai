import pytest
import os

from lightspeed_agents.message_bus.file_store import FileStore, FileLock


def test_file_store_save_and_load(tmp_path):
    store = FileStore(str(tmp_path))
    store.save("test.json", [{"id": "1", "name": "hello"}])
    loaded = store.load("test.json")
    assert len(loaded) == 1
    assert loaded[0]["name"] == "hello"


def test_file_store_load_missing(tmp_path):
    store = FileStore(str(tmp_path))
    assert store.load("nonexistent.json") == []


def test_file_store_exists(tmp_path):
    store = FileStore(str(tmp_path))
    assert store.exists("test.json") is False
    store.save("test.json", [{"id": "1"}])
    assert store.exists("test.json") is True


def test_file_store_delete(tmp_path):
    store = FileStore(str(tmp_path))
    store.save("test.json", [{"id": "1"}])
    store.delete("test.json")
    assert store.exists("test.json") is False


def test_file_store_append(tmp_path):
    store = FileStore(str(tmp_path))
    store.append("test.json", {"id": "1"})
    store.append("test.json", {"id": "2"})
    loaded = store.load("test.json")
    assert len(loaded) == 2


def test_file_store_update_entry(tmp_path):
    store = FileStore(str(tmp_path))
    store.save("test.json", [{"id": "1", "status": "pending"}])
    store.update_entry("test.json", "1", {"status": "done"})
    loaded = store.load("test.json")
    assert loaded[0]["status"] == "done"


def test_file_store_update_nonexistent(tmp_path):
    store = FileStore(str(tmp_path))
    store.save("test.json", [{"id": "1"}])
    store.update_entry("test.json", "999", {"status": "done"})
    loaded = store.load("test.json")
    assert loaded[0]["id"] == "1"


def test_file_store_backup(tmp_path):
    store = FileStore(str(tmp_path))
    store.save("test.json", [{"id": "1"}])
    assert os.path.exists(str(tmp_path / "test.json.bak"))


def test_file_store_atomic_write(tmp_path):
    store = FileStore(str(tmp_path))
    store.save("test.json", [{"id": "1"}])
    store.save("test.json", [{"id": "2"}])
    loaded = store.load("test.json")
    assert len(loaded) == 1
    assert loaded[0]["id"] == "2"
    tmp_files = list(tmp_path.glob("*.tmp"))
    assert len(tmp_files) == 0


def test_file_lock_acquire_release(tmp_path):
    lock_path = str(tmp_path / "test")
    lock = FileLock(lock_path)
    lock.acquire()
    assert os.path.exists(lock_path + ".lock")
    lock.release()
    assert not os.path.exists(lock_path + ".lock")


def test_file_lock_context_manager(tmp_path):
    lock_path = str(tmp_path / "test")
    with FileLock(lock_path):
        assert os.path.exists(lock_path + ".lock")
    assert not os.path.exists(lock_path + ".lock")
