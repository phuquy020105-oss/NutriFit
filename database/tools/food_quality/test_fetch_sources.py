from pathlib import Path
import tempfile
import unittest
from fetch_sources import safe_target, verify_file


class SourceCacheSafetyTest(unittest.TestCase):
    def test_relative_source_path_cannot_escape_cache(self):
        with tempfile.TemporaryDirectory() as root:
            for path in ("../outside", "/absolute", "C:/outside", "nin-searches/../../outside", "..\\outside"):
                with self.assertRaises(ValueError):
                    safe_target(root,path)
            self.assertEqual(Path(root).resolve()/"nin-searches/file.json",safe_target(root,"nin-searches/file.json"))

    def test_changed_response_is_not_accepted_under_old_source_hash(self):
        with tempfile.TemporaryDirectory() as root:
            f=Path(root)/"source.json";f.write_bytes(b"changed source")
            with self.assertRaisesRegex(ValueError,"checksum"):
                verify_file(f,"0"*64)
            self.assertEqual(b"changed source",f.read_bytes())


if __name__=="__main__":
    unittest.main()
