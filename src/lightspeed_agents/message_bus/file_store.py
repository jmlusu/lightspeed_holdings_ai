import binascii
import json
import os
import shutil
import tempfile
import time


class FileLock:
    def __init__(self, path: str, timeout: int = 10, stale_timeout: int = 30):
        self.lock_path = path + ".lock"
        self.timeout = timeout
        self.stale_timeout = stale_timeout
        self._acquired = False

    def acquire(self):
        start = time.time()
        while True:
            try:
                fd = os.open(
                    self.lock_path,
                    os.O_CREAT | os.O_EXCL | os.O_WRONLY,
                )
                try:
                    os.write(fd, str(os.getpid()).encode())
                finally:
                    os.close(fd)
                self._acquired = True
                return
            except FileExistsError:
                if os.path.exists(self.lock_path):
                    age = time.time() - os.path.getmtime(self.lock_path)
                    if age > self.stale_timeout:
                        try:
                            os.remove(self.lock_path)
                        except OSError:
                            pass
                        continue
                if time.time() - start > self.timeout:
                    raise TimeoutError(f"Could not acquire lock on {self.lock_path}")
                time.sleep(0.05)

    def release(self):
        self._acquired = False
        if os.path.exists(self.lock_path):
            try:
                os.remove(self.lock_path)
            except OSError:
                pass

    def __enter__(self):
        self.acquire()
        return self

    def __exit__(self, *args):
        self.release()


class FileStore:
    def __init__(self, directory: str):
        self.directory = directory
        os.makedirs(directory, exist_ok=True)

    def _path(self, filename: str) -> str:
        return os.path.join(self.directory, filename)

    def _lock(self, filename: str) -> FileLock:
        return FileLock(self._path(filename))

    def load(self, filename: str) -> list[dict]:
        path = self._path(filename)
        if not os.path.exists(path):
            return []
        with open(path, "r", encoding="utf-8") as f:
            raw = json.load(f)
        if isinstance(raw, dict) and "checksum" in raw and "data" in raw:
            stored = raw["checksum"]
            payload = json.dumps(raw["data"], indent=2, sort_keys=False)
            computed = format(binascii.crc32(payload.encode("utf-8")) & 0xFFFFFFFF, "08x")
            if stored != computed:
                backup = path + ".bak"
                if os.path.exists(backup):
                    with open(backup, "r", encoding="utf-8") as bf:
                        fallback = json.load(bf)
                    if isinstance(fallback, dict) and "data" in fallback:
                        return fallback["data"]
                    return fallback if isinstance(fallback, list) else []
                return []
            return raw["data"]
        return raw

    def save(self, filename: str, data: list[dict]):
        with self._lock(filename):
            path = self._path(filename)
            payload = json.dumps(data, indent=2, sort_keys=False)
            checksum = format(binascii.crc32(payload.encode("utf-8")) & 0xFFFFFFFF, "08x")
            envelope = {"checksum": checksum, "data": data}
            tmp_fd, tmp_path = tempfile.mkstemp(
                dir=self.directory,
                suffix=".tmp",
            )
            try:
                with os.fdopen(tmp_fd, "w", encoding="utf-8") as f:
                    json.dump(envelope, f, indent=2)
                    f.flush()
                    os.fsync(f.fileno())
                os.replace(tmp_path, path)
                self._backup(filename)
            except Exception:
                if os.path.exists(tmp_path):
                    os.remove(tmp_path)
                raise

    def _backup(self, filename: str):
        src = self._path(filename)
        dst = src + ".bak"
        if os.path.exists(src):
            shutil.copy2(src, dst)

    def append(self, filename: str, entry: dict):
        with self._lock(filename):
            entries = self._load_unlocked(filename)
            entries.append(entry)
            path = self._path(filename)
            tmp_fd, tmp_path = tempfile.mkstemp(
                dir=self.directory,
                suffix=".tmp",
            )
            try:
                with os.fdopen(tmp_fd, "w", encoding="utf-8") as f:
                    json.dump(entries, f, indent=2)
                    f.flush()
                    os.fsync(f.fileno())
                os.replace(tmp_path, path)
                self._backup(filename)
            except Exception:
                if os.path.exists(tmp_path):
                    os.remove(tmp_path)
                raise

    def _load_unlocked(self, filename: str) -> list[dict]:
        path = self._path(filename)
        if not os.path.exists(path):
            return []
        with open(path, "r", encoding="utf-8") as f:
            raw = json.load(f)
        if isinstance(raw, dict) and "data" in raw:
            return raw["data"]
        return raw if isinstance(raw, list) else []

    def update_entry(self, filename: str, entry_id: str, updates: dict):
        with self._lock(filename):
            entries = self._load_unlocked(filename)
            for i, entry in enumerate(entries):
                if entry.get("id") == entry_id:
                    entries[i].update(updates)
                    break
            else:
                return
            path = self._path(filename)
            tmp_fd, tmp_path = tempfile.mkstemp(
                dir=self.directory,
                suffix=".tmp",
            )
            try:
                with os.fdopen(tmp_fd, "w", encoding="utf-8") as f:
                    json.dump(entries, f, indent=2)
                    f.flush()
                    os.fsync(f.fileno())
                os.replace(tmp_path, path)
                self._backup(filename)
            except Exception:
                if os.path.exists(tmp_path):
                    os.remove(tmp_path)
                raise

    def delete(self, filename: str):
        with self._lock(filename):
            path = self._path(filename)
            if os.path.exists(path):
                os.remove(path)

    def exists(self, filename: str) -> bool:
        return os.path.exists(self._path(filename))
