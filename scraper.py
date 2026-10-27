import os
import json
import feedparser
import gspread
from google.oauth2.service_account import Credentials
import datetime

# Configuration
RSS_URL = 'https://www.reddit.com/r/shortdrama/search.rss?q=AI&sort=new'
SHEET_ID = '1W07Fdlfj0HRPvqSna04b956xlestkLCZboKKyvWqxC4'
USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'

def get_google_sheets_client():
    # Attempt to read credentials from environment variable
    credentials_json = os.environ.get('GCP_SERVICE_ACCOUNT_JSON')
    if not credentials_json:
        print("Warning: GCP_SERVICE_ACCOUNT_JSON environment variable not found. Running without gspread integration for testing.")
        return None
    
    try:
        creds_dict = json.loads(credentials_json)
        scopes = [
            'https://www.googleapis.com/auth/spreadsheets',
            'https://www.googleapis.com/auth/drive'
        ]
        creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
        client = gspread.authorize(creds)
        return client
    except Exception as e:
        print(f"Error authenticating with Google Sheets: {e}")
        return None

def fetch_reddit_rss(url):
    # Reddit sometimes blocks requests without a custom user agent
    d = feedparser.parse(url, agent=USER_AGENT)
    return d.entries

def extract_genre(entry):
    # Try to extract genre from tags/categories if present
    if hasattr(entry, 'tags'):
        tags = [tag.term for tag in entry.tags]
        if tags:
            return ", ".join(tags)
    return "N/A"

def append_to_sheet(client, rows):
    if not client:
        return
    
    try:
        sheet = client.open_by_key(SHEET_ID).sheet1
        if rows:
            sheet.append_rows(rows)
            print(f"Successfully appended {len(rows)} rows to the Google Sheet.")
        else:
            print("No new rows to append.")
    except gspread.GSpreadException as e:
        print(f"Error appending to Google Sheets: {e}")

def main():
    entries = fetch_reddit_rss(RSS_URL)
    print(f"Found {len(entries)} entries in the RSS feed.")
    
    rows_to_append = []
    for entry in entries:
        title = entry.title if hasattr(entry, 'title') else 'No Title'
        link = entry.link if hasattr(entry, 'link') else 'No Link'
        genre = extract_genre(entry)
        date = entry.published if hasattr(entry, 'published') else datetime.datetime.utcnow().isoformat()
        
        row = [title, link, genre, date]
        rows_to_append.append(row)
        
        # Log to console for verification
        print(f"Scraped: {title} | {link} | {genre} | {date}")
        
    client = get_google_sheets_client()
    if client:
        append_to_sheet(client, rows_to_append)
    else:
        print("Skipping Google Sheets append because client could not be initialized.")

if __name__ == '__main__':
    main()
