import pytest
from unittest.mock import patch, MagicMock
import datetime

import scraper

def test_extract_genre_with_tags():
    mock_entry = MagicMock()
    mock_tag1 = MagicMock()
    mock_tag1.term = "Tag1"
    mock_tag2 = MagicMock()
    mock_tag2.term = "Tag2"
    mock_entry.tags = [mock_tag1, mock_tag2]

    assert scraper.extract_genre(mock_entry) == "Tag1, Tag2"

def test_extract_genre_empty_tags():
    mock_entry = MagicMock()
    mock_entry.tags = []

    assert scraper.extract_genre(mock_entry) == "N/A"

def test_extract_genre_no_tags():
    class EntryWithoutTags:
        pass

    mock_entry = EntryWithoutTags()
    assert scraper.extract_genre(mock_entry) == "N/A"


class EntryWithoutAttributes:
    pass

@patch('scraper.fetch_reddit_rss')
@patch('scraper.get_google_sheets_client')
@patch('scraper.datetime')
def test_main_missing_attributes(mock_datetime, mock_get_client, mock_fetch_rss, capsys):
    # Setup mock date for reliable assertion
    mock_now = datetime.datetime(2023, 1, 1, 12, 0, 0)
    mock_datetime.datetime.utcnow.return_value = mock_now

    # Setup empty mock entry that doesn't have title, link, published, or tags
    mock_entry = EntryWithoutAttributes()
    mock_fetch_rss.return_value = [mock_entry]

    # We want get_google_sheets_client to return None so it doesn't try to append
    mock_get_client.return_value = None

    scraper.main()

    captured = capsys.readouterr()

    # Check if fallback values were applied and printed properly
    assert "No Title" in captured.out
    assert "No Link" in captured.out
    assert "N/A" in captured.out
    assert mock_now.isoformat() in captured.out
    assert f"Scraped: No Title | No Link | N/A | {mock_now.isoformat()}" in captured.out
