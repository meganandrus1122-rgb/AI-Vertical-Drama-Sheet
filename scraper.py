import os
import json
import feedparser
import gspread
import urllib.request
from bs4 import BeautifulSoup
from google.oauth2.service_account import Credentials
import datetime
import time
import re

# Configuration
RSS_URLS = [
    'https://www.reddit.com/r/Vertical_Dramas/new.rss',
    'https://www.reddit.com/r/nsfw_Vertical_AI/new.rss'
]
SHEET_ID = '1W07Fdlfj0HRPvqSna04b956xlestkLCZboKKyvWqxC4'
USER_AGENT = 'python:ai-vertical-drama-scraper:v1.3 (by /u/meganandrus)'

GENRE_KEYWORDS = [
    'mafia', 'ceo', 'alpha', 'werewolf', 'billionaire', 'revenge', 
    'vampire', 'contract marriage', 'arranged marriage', 'enemies to lovers',
    'boss', 'pregnant', 'secret baby', 'rejection', 'mate', 'luna',
    'sweet', 'angst', 'time travel', 'rebirth', 'reincarnation'
]

def get_google_sheets_client():
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

def extract_link(entry):
    reddit_link = entry.link if hasattr(entry, 'link') else 'No Link'
    
    if hasattr(entry, 'content') and entry.content:
        html_content = entry.content[0].value
        soup = BeautifulSoup(html_content, 'html.parser')
        for a in soup.find_all('a', href=True):
            href = a['href']
            # Exclude standard Reddit links from being identified as the drama link
            if 'reddit.com' not in href and 'redd.it' not in href:
                return href # Return the first external link found
                
    return reddit_link

def extract_genre(entry):
    found_genres = set()
    text_to_search = (getattr(entry, 'title', '') + " " + getattr(entry, 'summary', '')).lower()
    
    if hasattr(entry, 'content') and entry.content:
        text_to_search += " " + entry.content[0].value.lower()
        
    for keyword in GENRE_KEYWORDS:
        if re.search(r'\b' + re.escape(keyword) + r'\b', text_to_search):
            found_genres.add(keyword.title())
            
    if found_genres:
        return ", ".join(sorted(found_genres))
        
    return "Unknown/Other"


def sanitize_for_sheets(value):
    if isinstance(value, str) and value and value[0] in ('=', '+', '-', '@'):
        return "'" + value
    return value

def append_to_sheet(client, rows):
    if not client:
        return
    try:
        sheet = client.open_by_key(SHEET_ID).sheet1
        if rows:
            sanitized_rows = [[sanitize_for_sheets(item) for item in row] for row in rows]
            sheet.append_rows(sanitized_rows)
            print(f"Successfully appended {len(sanitized_rows)} rows to the Google Sheet.")
        else:
            print("No new rows to append.")
    except Exception as e:
        print(f"Error appending to Google Sheets: {e}")

def main():
    all_entries = []
    
    for url in RSS_URLS:
        entries = fetch_reddit_rss(url)
        print(f"Found {len(entries)} entries in {url}")
        all_entries.extend(entries)
        time.sleep(2)
        
    search_url = 'https://www.reddit.com/r/shortdrama/search.rss?q=AI&sort=new'
    search_entries = fetch_reddit_rss(search_url)
    print(f"Found {len(search_entries)} entries in {search_url}")
    all_entries.extend(search_entries)
    
    rows_to_append = []
    for entry in all_entries:
        title = entry.title if hasattr(entry, 'title') else 'No Title'
        link = extract_link(entry)
        genre = extract_genre(entry)
        
        try:
            # Parse the published string if it exists to clean it up
            if hasattr(entry, 'published_parsed') and entry.published_parsed:
                date = time.strftime('%Y-%m-%d', entry.published_parsed)
            else:
                date = datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%d')
        except:
            date = datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%d')
        
        # Order: Title, Link, Genre, Date Added
        row = [title, link, genre, date]
        rows_to_append.append(row)
        
        print(f"Scraped: {title} | {link} | {genre} | {date}")
        
    client = get_google_sheets_client()
    if client:
        append_to_sheet(client, rows_to_append)
    else:
        print("Skipping Google Sheets append because client could not be initialized.")

if __name__ == '__main__':
    main()
