import os
import json
import feedparser
import gspread
import urllib.request
from google.oauth2.service_account import Credentials
import datetime
import time

# Configuration
RSS_URLS = [
    'https://www.reddit.com/r/Vertical_Dramas/new.rss',
    'https://www.reddit.com/r/nsfw_Vertical_AI/new.rss'
]
SHEET_ID = '1W07Fdlfj0HRPvqSna04b956xlestkLCZboKKyvWqxC4'
USER_AGENT = 'python:ai-vertical-drama-scraper:v1.1 (by /u/meganandrus)'

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
    # Fetch content using urllib first to cleanly bypass feedparser blocking issues on 429
    req = urllib.request.Request(url, headers={'User-Agent': USER_AGENT})
    try:
        with urllib.request.urlopen(req) as response:
            content = response.read()
            d = feedparser.parse(content)
            return d.entries
    except urllib.error.HTTPError as e:
        print(f"HTTP Error fetching {url}: {e.code} {e.reason}")
        return []
    except Exception as e:
        print(f"Error fetching {url}: {e}")
        return []

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
    except Exception as e:
        print(f"Error appending to Google Sheets: {e}")

def main():
    all_entries = []
    
    # Notice: the search URL https://www.reddit.com/r/shortdrama/search.rss?q=AI&sort=new currently returns a 404 block page.
    # Therefore, we fetch from the known working ones first.
    for url in RSS_URLS:
        entries = fetch_reddit_rss(url)
        print(f"Found {len(entries)} entries in {url}")
        all_entries.extend(entries)
        time.sleep(2) # Throttle to respect Reddit API rate limits
        
    # We attempt the search URL individually and swallow the error if it fails
    search_url = 'https://www.reddit.com/r/shortdrama/search.rss?q=AI&sort=new'
    search_entries = fetch_reddit_rss(search_url)
    print(f"Found {len(search_entries)} entries in {search_url}")
    all_entries.extend(search_entries)
    
    rows_to_append = []
    for entry in all_entries:
        title = entry.title if hasattr(entry, 'title') else 'No Title'
        link = entry.link if hasattr(entry, 'link') else 'No Link'
        genre = extract_genre(entry)
        date = entry.published if hasattr(entry, 'published') else datetime.datetime.utcnow().isoformat()
        
        row = [title, link, genre, date]
        rows_to_append.append(row)
        
        # Log to console for verification
        # print(f"Scraped: {title} | {link} | {genre} | {date}")
        
    client = get_google_sheets_client()
    if client:
        append_to_sheet(client, rows_to_append)
    else:
        print("Skipping Google Sheets append because client could not be initialized.")

if __name__ == '__main__':
    main()
