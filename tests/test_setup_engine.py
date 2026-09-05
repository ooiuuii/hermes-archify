"""Installation must authenticate bytes before extracting or executing anything."""

import hashlib
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import zipfile

import setup_engine


class SetupTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="archify-setup-test-")
        self.root = Path(self.temp.name)
        self.root_patch = patch.object(setup_engine, "ROOT", self.root)
        self.root_patch.start()

    def tearDown(self):
        self.root_patch.stop()
        self.temp.cleanup()

    def archive(self, extra=None):
        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, "w") as package:
            package.writestr("archify/bin/archify.mjs", "// never executed by installation")
            package.writestr("archify/package.json", '{"version":"2.16.0"}')
            package.writestr("archify/LICENSE", "upstream license remains intact")
            if extra:
                member, content = extra
                if isinstance(member, str):
                    # ZipInfo normally rewrites backslashes on Windows. Retain
                    # raw member names to test an archive made by another OS.
                    info = zipfile.ZipInfo("entry")
                    info.filename = member
                    member = info
                package.writestr(member, content)
        data = buffer.getvalue()
        archive = self.root / "engine.zip"
        archive.write_bytes(data)
        (self.root / "engine-lock.json").write_text(json.dumps({
            "version": "v2.16.0", "url": "https://example.invalid/not-called",
            "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest(),
        }), encoding="utf-8")
        return archive

    def test_verified_archive_keeps_upstream_files_and_refuses_overwrite(self):
        archive = self.archive(("archify/brand-marks/README.md", "brand license notes"))
        result = setup_engine.install(archive)
        self.assertTrue(result["ok"])
        engine = Path(result["engine_dir"])
        self.assertEqual((engine / "brand-marks/README.md").read_text(), "brand license notes")
        self.assertTrue((engine / "hermes-install-receipt.json").is_file())
        with self.assertRaisesRegex(ValueError, "already exists"):
            setup_engine.install(archive)
        self.assertEqual((engine / "LICENSE").read_text(), "upstream license remains intact")

    def test_corrupted_archive_is_rejected_before_extraction(self):
        archive = self.archive()
        archive.write_bytes(archive.read_bytes() + b"tampered")
        with self.assertRaisesRegex(ValueError, "SHA-256"):
            setup_engine.install(archive)
        self.assertFalse((self.root / ".engine").exists())

    def test_unsafe_members_are_not_extracted(self):
        for member in ("../outside", "archify/../../outside", "/absolute", "C:/outside", "archify\\bad"):
            with self.subTest(member=member):
                archive = self.archive((member, "unsafe"))
                with self.assertRaisesRegex(ValueError, "Unsafe archive"):
                    setup_engine.install(archive)
                self.assertFalse((self.root / ".engine/archify").exists())

    def test_symlinks_are_not_extracted(self):
        info = zipfile.ZipInfo("archify/link")
        info.create_system = 3
        info.external_attr = (0o120777 << 16)
        archive = self.archive((info, "../../outside"))
        with self.assertRaisesRegex(ValueError, "Unsafe archive"):
            setup_engine.install(archive)


if __name__ == "__main__":
    unittest.main()
