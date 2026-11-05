import hashlib
import tempfile
import unittest
from pathlib import Path

from generator.fetch import ChecksumError, Source, fetch_all


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


class FakeDownload:
    def __init__(self, payloads: dict[str, bytes]):
        self.payloads = payloads
        self.calls: list[str] = []

    def __call__(self, url: str) -> bytes:
        self.calls.append(url)
        return self.payloads[url]


class FetchTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.cache = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def test_downloads_and_writes_file_matching_its_pin(self):
        download = FakeDownload({"u/a": b"alpha"})
        fetch_all([Source("a.csv", "u/a", sha(b"alpha"))], self.cache, download)
        self.assertEqual((self.cache / "a.csv").read_bytes(), b"alpha")

    def test_second_run_uses_cache_without_downloading(self):
        download = FakeDownload({"u/a": b"alpha"})
        sources = [Source("a.csv", "u/a", sha(b"alpha"))]
        fetch_all(sources, self.cache, download)
        fetch_all(sources, self.cache, download)
        self.assertEqual(download.calls, ["u/a"])

    def test_changed_upstream_file_stops_and_writes_nothing(self):
        download = FakeDownload({"u/a": b"changed"})
        with self.assertRaisesRegex(ChecksumError, "a.csv"):
            fetch_all([Source("a.csv", "u/a", sha(b"alpha"))], self.cache, download)
        self.assertFalse((self.cache / "a.csv").exists())

    def test_corrupt_cached_file_stops_without_overwriting_it(self):
        (self.cache / "a.csv").write_bytes(b"corrupt")
        download = FakeDownload({"u/a": b"alpha"})
        with self.assertRaisesRegex(ChecksumError, "a.csv"):
            fetch_all([Source("a.csv", "u/a", sha(b"alpha"))], self.cache, download)
        self.assertEqual((self.cache / "a.csv").read_bytes(), b"corrupt")
        self.assertEqual(download.calls, [])

    def test_failure_on_later_source_keeps_earlier_verified_files(self):
        download = FakeDownload({"u/a": b"alpha", "u/b": b"wrong"})
        sources = [Source("a.csv", "u/a", sha(b"alpha")), Source("b.csv", "u/b", sha(b"beta"))]
        with self.assertRaises(ChecksumError):
            fetch_all(sources, self.cache, download)
        self.assertTrue((self.cache / "a.csv").exists())
        self.assertFalse((self.cache / "b.csv").exists())


if __name__ == "__main__":
    unittest.main()
