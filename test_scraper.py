import unittest
from unittest.mock import MagicMock, patch
import io
import scraper

class TestScraper(unittest.TestCase):
    def test_append_to_sheet_error(self):
        # Arrange
        mock_client = MagicMock()
        mock_sheet = MagicMock()

        # Mock open_by_key to return an object with a sheet1 property
        mock_open = MagicMock()
        mock_open.sheet1 = mock_sheet
        mock_client.open_by_key.return_value = mock_open

        # Configure append_rows to raise an Exception
        mock_sheet.append_rows.side_effect = Exception("Test Google Sheets API Error")

        rows = [["row1_col1", "row1_col2"]]

        with patch('sys.stdout', new_callable=io.StringIO) as captured_output:
            # Act
            scraper.append_to_sheet(mock_client, rows)

            # Assert
            mock_client.open_by_key.assert_called_once_with(scraper.SHEET_ID)
            mock_sheet.append_rows.assert_called_once_with(rows)

            output = captured_output.getvalue()
            self.assertIn("Error appending to Google Sheets: Test Google Sheets API Error", output)

if __name__ == '__main__':
    unittest.main()
