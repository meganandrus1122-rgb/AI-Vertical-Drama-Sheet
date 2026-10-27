import unittest
from unittest.mock import patch, MagicMock, call
import json
import os
import datetime

import scraper

class TestScraper(unittest.TestCase):

    @patch('scraper.os.environ.get')
    def test_get_google_sheets_client_no_creds(self, mock_env_get):
        mock_env_get.return_value = None
        client = scraper.get_google_sheets_client()
        self.assertIsNone(client)
        mock_env_get.assert_called_with('GCP_SERVICE_ACCOUNT_JSON')

    @patch('scraper.gspread.authorize')
    @patch('scraper.Credentials.from_service_account_info')
    @patch('scraper.os.environ.get')
    def test_get_google_sheets_client_with_creds(self, mock_env_get, mock_creds, mock_authorize):
        mock_env_get.return_value = json.dumps({"project_id": "test"})
        mock_creds.return_value = "mock_credentials"
        mock_authorize.return_value = "mock_client"

        client = scraper.get_google_sheets_client()

        self.assertEqual(client, "mock_client")
        mock_creds.assert_called_once()
        mock_authorize.assert_called_with("mock_credentials")

    @patch('scraper.os.environ.get')
    def test_get_google_sheets_client_invalid_json(self, mock_env_get):
        mock_env_get.return_value = "invalid json"
        client = scraper.get_google_sheets_client()
        self.assertIsNone(client)

    @patch('scraper.feedparser.parse')
    def test_fetch_reddit_rss(self, mock_parse):
        mock_parse.return_value = MagicMock(entries=['entry1', 'entry2'])
        url = "http://test.url"
        entries = scraper.fetch_reddit_rss(url)
        self.assertEqual(entries, ['entry1', 'entry2'])
        mock_parse.assert_called_with(url, agent=scraper.USER_AGENT)

    def test_extract_genre_with_tags(self):
        class MockTag:
            def __init__(self, term):
                self.term = term

        class MockEntry:
            def __init__(self, tags):
                self.tags = tags

        entry = MockEntry([MockTag("AI"), MockTag("Drama")])
        genre = scraper.extract_genre(entry)
        self.assertEqual(genre, "AI, Drama")

    def test_extract_genre_without_tags(self):
        class MockEntry:
            pass

        entry = MockEntry()
        genre = scraper.extract_genre(entry)
        self.assertEqual(genre, "N/A")

    def test_extract_genre_empty_tags(self):
        class MockEntry:
            def __init__(self):
                self.tags = []

        entry = MockEntry()
        genre = scraper.extract_genre(entry)
        self.assertEqual(genre, "N/A")

    def test_append_to_sheet_no_client(self):
        # Should return early without exceptions
        scraper.append_to_sheet(None, [["row1"]])

    def test_append_to_sheet_with_client_and_rows(self):
        mock_client = MagicMock()
        mock_sheet = MagicMock()
        mock_client.open_by_key.return_value.sheet1 = mock_sheet

        rows = [["title", "link", "genre", "date"]]
        scraper.append_to_sheet(mock_client, rows)

        mock_client.open_by_key.assert_called_with(scraper.SHEET_ID)
        mock_sheet.append_rows.assert_called_with(rows)

    def test_append_to_sheet_with_client_no_rows(self):
        mock_client = MagicMock()
        mock_sheet = MagicMock()
        mock_client.open_by_key.return_value.sheet1 = mock_sheet

        scraper.append_to_sheet(mock_client, [])

        mock_client.open_by_key.assert_called_with(scraper.SHEET_ID)
        mock_sheet.append_rows.assert_not_called()

    def test_append_to_sheet_exception(self):
        mock_client = MagicMock()
        mock_client.open_by_key.side_effect = Exception("Test exception")

        # Should catch exception and print, but not raise
        scraper.append_to_sheet(mock_client, [["row1"]])

    @patch('scraper.get_google_sheets_client')
    @patch('scraper.append_to_sheet')
    @patch('scraper.fetch_reddit_rss')
    @patch('scraper.datetime')
    def test_main(self, mock_datetime, mock_fetch, mock_append, mock_get_client):
        # Mocking the RSS entries
        class MockEntry:
            def __init__(self, title, link, tags, published):
                if title is not None: self.title = title
                if link is not None: self.link = link
                if tags is not None:
                    class MockTag:
                        def __init__(self, term): self.term = term
                    self.tags = [MockTag(t) for t in tags]
                if published is not None: self.published = published

        # Setup mocks
        mock_fetch.return_value = [
            MockEntry("Title 1", "Link 1", ["AI"], "Date 1"),
            MockEntry(None, None, None, None) # Edge case for missing attributes
        ]
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        # Mock UTC now for the edge case entry
        mock_now = datetime.datetime(2023, 1, 1)
        mock_datetime.datetime.utcnow.return_value = mock_now

        # Run main
        scraper.main()

        # Assertions
        mock_fetch.assert_called_with(scraper.RSS_URL)
        mock_get_client.assert_called_once()

        expected_rows = [
            ["Title 1", "Link 1", "AI", "Date 1"],
            ["No Title", "No Link", "N/A", mock_now.isoformat()]
        ]
        mock_append.assert_called_with(mock_client, expected_rows)

if __name__ == '__main__':
    unittest.main()
