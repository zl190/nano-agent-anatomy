"""
Tests for memory_v0 and memory_v1.
Tests are structural and deterministic — no API key required.

Note: memory_v1._write_memory uses a module-level INDEX_FILE constant.
Tests patch it to a temp directory to avoid polluting ~/.agent-anatomy/.
"""

import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).parent.parent))

from memory_v0 import MemoryStore as MemoryStoreV0
import memory_v1


class TestMemoryV0AppendOnly(unittest.TestCase):
    def test_append_stores_entries(self):
        store = MemoryStoreV0()
        store.save("key1", "summary1")
        store.save("key2", "summary2")
        loaded = store.load()
        self.assertIn("key1", loaded)
        self.assertIn("key2", loaded)

    def test_no_dedup_on_duplicate_save(self):
        store = MemoryStoreV0()
        store.save("key1", "summary1")
        store.save("key1", "summary1")
        # v0 has no dedup — both entries should be present
        self.assertEqual(len(store._entries), 2)

    def test_empty_store_returns_empty_string(self):
        store = MemoryStoreV0()
        self.assertEqual(store.load(), "")

    def test_save_increments_entry_count(self):
        store = MemoryStoreV0()
        for i in range(5):
            store.save(f"key_{i}", f"summary {i}")
        self.assertEqual(len(store._entries), 5)


class TestMemoryV1FilePersistence(unittest.TestCase):
    def _make_store(self, tmpdir: str):
        """Create a MemoryStoreV1 patched so INDEX_FILE points into tmpdir."""
        tmp_path = Path(tmpdir)
        index_path = tmp_path / "MEMORY.md"
        with mock.patch.object(memory_v1, "INDEX_FILE", index_path):
            store = memory_v1.MemoryStore(tmp_path)
        return store, tmp_path, index_path

    def test_save_creates_individual_file(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            index_path = tmp_path / "MEMORY.md"
            with mock.patch.object(memory_v1, "INDEX_FILE", index_path):
                store = memory_v1.MemoryStore(tmp_path)
                store.save("test_key", "test summary")
            self.assertTrue((tmp_path / "test_key.md").exists())

    def test_save_updates_index(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            index_path = tmp_path / "MEMORY.md"
            with mock.patch.object(memory_v1, "INDEX_FILE", index_path):
                store = memory_v1.MemoryStore(tmp_path)
                store.save("test_key", "test summary")
            index = index_path.read_text()
            self.assertIn("test_key", index)

    def test_index_stays_under_max_lines(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            index_path = tmp_path / "MEMORY.md"
            with mock.patch.object(memory_v1, "INDEX_FILE", index_path):
                store = memory_v1.MemoryStore(tmp_path)
                for i in range(60):  # exceed MAX_INDEX_LINES (50)
                    store.save(f"key_{i}", f"summary {i}")
            index = index_path.read_text()
            non_empty_lines = [l for l in index.strip().split("\n") if l.strip()]
            # 50 entries max + 1 header line
            self.assertLessEqual(len(non_empty_lines), 51)

    def test_no_duplicate_index_entries_on_same_key(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            index_path = tmp_path / "MEMORY.md"
            with mock.patch.object(memory_v1, "INDEX_FILE", index_path):
                store = memory_v1.MemoryStore(tmp_path)
                store.save("same_key", "first value")
                store.save("same_key", "second value")
            index = index_path.read_text()
            self.assertEqual(index.count("[same_key]"), 1)

    def test_detail_file_contains_summary(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            index_path = tmp_path / "MEMORY.md"
            with mock.patch.object(memory_v1, "INDEX_FILE", index_path):
                store = memory_v1.MemoryStore(tmp_path)
                store.save("mykey", "this is my summary")
            content = (tmp_path / "mykey.md").read_text()
            self.assertIn("this is my summary", content)

    def test_load_reads_index_file(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            index_path = tmp_path / "MEMORY.md"
            with mock.patch.object(memory_v1, "INDEX_FILE", index_path):
                store = memory_v1.MemoryStore(tmp_path)
                store.save("loadkey", "load test")
                loaded = store.load()
            self.assertIn("loadkey", loaded)


if __name__ == "__main__":
    unittest.main()
