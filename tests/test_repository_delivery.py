import io
import unittest
import zipfile
from scripts.download_ami import safe_members
from scripts.run_review_workspace import optional_log


class DeliveryTests(unittest.TestCase):
    def test_demo_does_not_require_private_raw_log(self):
        self.assertEqual(optional_log({"raw_log_path": "outputs/raw_api/not-shipped.json"}), {})
        self.assertEqual(optional_log({}), {})

    def test_rejects_zip_path_traversal(self):
        data = io.BytesIO()
        with zipfile.ZipFile(data, "w") as archive:
            archive.writestr("../secret.txt", "bad")
        with zipfile.ZipFile(data) as archive:
            with self.assertRaises(ValueError):
                safe_members(archive)

    def test_rejects_zip_symlinks(self):
        data = io.BytesIO()
        entry = zipfile.ZipInfo("link")
        entry.external_attr = 0o120777 << 16
        with zipfile.ZipFile(data, "w") as archive:
            archive.writestr(entry, "outside")
        with zipfile.ZipFile(data) as archive:
            with self.assertRaises(ValueError):
                safe_members(archive)

    def test_normal_archive_accepted(self):
        data = io.BytesIO()
        with zipfile.ZipFile(data, "w") as archive:
            archive.writestr("words/example.xml", "<root/>")
        with zipfile.ZipFile(data) as archive:
            self.assertEqual(len(safe_members(archive)), 1)
