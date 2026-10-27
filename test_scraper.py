import unittest
from unittest.mock import Mock
from scraper import extract_genre

class TestExtractGenre(unittest.TestCase):
    def test_no_tags_attribute(self):
        # Entry without 'tags' attribute
        entry = Mock(spec=[])
        result = extract_genre(entry)
        self.assertEqual(result, "N/A")

    def test_empty_tags_list(self):
        # Entry with empty 'tags' list
        entry = Mock()
        entry.tags = []
        result = extract_genre(entry)
        self.assertEqual(result, "N/A")

    def test_single_tag(self):
        # Entry with a single tag
        entry = Mock()
        tag = Mock()
        tag.term = "drama"
        entry.tags = [tag]
        result = extract_genre(entry)
        self.assertEqual(result, "drama")

    def test_multiple_tags(self):
        # Entry with multiple tags
        entry = Mock()
        tag1 = Mock()
        tag1.term = "drama"
        tag2 = Mock()
        tag2.term = "ai"
        entry.tags = [tag1, tag2]
        result = extract_genre(entry)
        self.assertEqual(result, "drama, ai")

if __name__ == '__main__':
    unittest.main()
