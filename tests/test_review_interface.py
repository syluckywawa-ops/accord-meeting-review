import unittest
from collections import Counter
from html.parser import HTMLParser
from pathlib import Path


class InterfaceParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.ids = []
        self.styles = 0
        self.filters = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if 'id' in attrs:
            self.ids.append(attrs['id'])
        self.styles += tag == 'style'
        if 'data-filter' in attrs:
            self.filters.append(attrs['data-filter'])


class ReviewInterfaceTests(unittest.TestCase):
    def setUp(self):
        self.source = (Path(__file__).resolve().parents[1] / 'web/review.html').read_text()
        self.parser = InterfaceParser()
        self.parser.feed(self.source)

    def test_unique_control_ids_and_one_design_system(self):
        duplicates = [key for key, n in Counter(self.parser.ids).items() if n > 1]
        self.assertEqual(duplicates, [])
        self.assertEqual(self.parser.styles, 1)
        for key in ['meeting', 'condition', 'scan', 'json', 'csv', 'import-dialog',
                    'pending-count', 'approved-count', 'rejected-count']:
            self.assertIn(key, self.parser.ids)

    def test_product_brand_and_review_filters(self):
        self.assertIn('<title>Accord · Meeting workspace</title>', self.source)
        self.assertIn('Turn meeting conversations into verified action items.', self.source)
        self.assertNotIn('Occurred', self.source)
        self.assertEqual(self.parser.filters, ['all', 'pending', 'approved', 'rejected'])

    def test_upload_entry_belongs_to_meeting_selector(self):
        self.assertIn('class="meeting-field"', self.source)
        self.assertLess(self.source.index('id="meeting"'), self.source.index('id="open-import"'))
        self.assertIn("own.label='Your uploaded meetings'", self.source)
        self.assertIn("demos.label='Guided demos · saved research results'", self.source)
        self.assertIn("samples.label='More public AMI research meetings'", self.source)
        self.assertIn('id="meeting-guide"', self.source)
        self.assertIn('ES2004d:{label:', self.source)
        self.assertIn("state.source_status!=='valid'", self.source)
        self.assertIn('Local rules · unbenchmarked', self.source)
        self.assertNotIn('open-import-top', self.source)
