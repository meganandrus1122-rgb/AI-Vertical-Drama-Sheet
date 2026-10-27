import os
import json
from unittest.mock import patch, MagicMock
from scraper import get_google_sheets_client

def test_get_google_sheets_client_exception(capsys):
    with patch('os.environ.get') as mock_env_get, \
         patch('json.loads') as mock_json_loads:
        mock_env_get.return_value = '{"project_id": "test"}'
        mock_json_loads.side_effect = Exception("Test Exception")

        client = get_google_sheets_client()

        assert client is None
        captured = capsys.readouterr()
        assert "Error authenticating with Google Sheets: Test Exception" in captured.out

def test_get_google_sheets_client_missing_env_var(capsys):
    with patch('os.environ.get') as mock_env_get:
        mock_env_get.return_value = None

        client = get_google_sheets_client()

        assert client is None
        captured = capsys.readouterr()
        assert "Warning: GCP_SERVICE_ACCOUNT_JSON environment variable not found." in captured.out

def test_get_google_sheets_client_success():
    with patch('os.environ.get') as mock_env_get, \
         patch('json.loads') as mock_json_loads, \
         patch('scraper.Credentials.from_service_account_info') as mock_creds, \
         patch('scraper.gspread.authorize') as mock_authorize:

        mock_env_get.return_value = '{"project_id": "test"}'
        mock_json_loads.return_value = {"project_id": "test"}

        mock_creds_instance = MagicMock()
        mock_creds.return_value = mock_creds_instance

        mock_client = MagicMock()
        mock_authorize.return_value = mock_client

        client = get_google_sheets_client()

        assert client == mock_client
        mock_env_get.assert_called_once_with('GCP_SERVICE_ACCOUNT_JSON')
        mock_json_loads.assert_called_once_with('{"project_id": "test"}')
        mock_creds.assert_called_once_with({"project_id": "test"}, scopes=[
            'https://www.googleapis.com/auth/spreadsheets',
            'https://www.googleapis.com/auth/drive'
        ])
        mock_authorize.assert_called_once_with(mock_creds_instance)
