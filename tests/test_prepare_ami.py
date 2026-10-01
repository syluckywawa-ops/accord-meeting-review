import importlib.util
import sys
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path


MODULE_PATH = Path(__file__).parents[1] / "scripts" / "prepare_ami.py"
SPEC = importlib.util.spec_from_file_location("prepare_ami", MODULE_PATH)
prepare_ami = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
sys.modules[SPEC.name] = prepare_ami
SPEC.loader.exec_module(prepare_ami)


class PrepareAmiTests(unittest.TestCase):
    def test_timestamp(self):
        self.assertEqual(prepare_ami.timestamp(0.37), "00:00.37")
        self.assertEqual(prepare_ami.timestamp(125.5), "02:05.50")

    def test_mixed_ami_date_formats(self):
        self.assertEqual(prepare_ami.normalise_ami_date("15-12-04"), "2004-12-15")
        self.assertEqual(prepare_ami.normalise_ami_date("13-12-2004"), "2004-12-13")
        self.assertIsNone(prepare_ami.normalise_ami_date(""))

    def test_merge_only_adjacent_same_speaker(self):
        Segment = prepare_ami.Segment
        source = [
            Segment("A", "PM", 0.0, 1.0, "First.", ("s1",)),
            Segment("A", "PM", 1.2, 2.0, "Second.", ("s2",)),
            Segment("B", "ME", 2.1, 3.0, "Reply.", ("s3",)),
            Segment("A", "PM", 3.1, 4.0, "Third.", ("s4",)),
        ]
        merged = prepare_ami.merge_adjacent_segments(source)
        self.assertEqual(len(merged), 3)
        self.assertEqual(merged[0].text, "First. Second.")
        self.assertEqual(merged[0].source_ids, ("s1", "s2"))
        self.assertEqual(merged[2].text, "Third.")

    def test_plain_href_attribute_used_by_ami(self):
        child = ET.fromstring(
            '<nite:child xmlns:nite="http://nite.sourceforge.net/" '
            'href="sample.words.xml#id(sample.words0)..id(sample.words2)"/>'
        )
        href = child.get("href") or child.get(prepare_ami.NITE_HREF, "")
        match = prepare_ami.HREF_RANGE.search(href)
        self.assertIsNotNone(match)
        self.assertEqual(match.group(1), "sample.words0")
        self.assertEqual(match.group(2), "sample.words2")


if __name__ == "__main__":
    unittest.main()
