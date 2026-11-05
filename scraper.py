import os
import json
import feedparser
import gspread
import urllib.request
from bs4 import BeautifulSoup
from google.oauth2.service_account import Credentials
from google import genai
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

GENRE_REGEX = re.compile(r'\b(' + '|'.join(re.escape(k) for k in GENRE_KEYWORDS) + r')\b')

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

def extract_links(entry):
    source_link = entry.link if hasattr(entry, 'link') else 'No Link'
    watch_link = ''

    if hasattr(entry, 'content') and entry.content:
        html_content = entry.content[0].value
        soup = BeautifulSoup(html_content, 'html.parser')
        for a in soup.find_all('a', href=True):
            href = a['href']
            # Exclude standard Reddit links from being identified as the drama link
            if 'reddit.com' not in href and 'redd.it' not in href:
                watch_link = href
                break # Return the first external link found as watch link

    return source_link, watch_link

def get_gemini_client():
    api_key = os.environ.get('GEMINI_API_KEY')
    if not api_key:
        print("Warning: GEMINI_API_KEY not found. Using fallback genre extraction.")
        return None
    try:
        return genai.Client(api_key=api_key)
    except Exception as e:
        print(f"Error initializing Gemini client: {e}")
        return None


def extract_fallback(entry):
    text_to_search = (getattr(entry, 'title', '') + " " + getattr(entry, 'summary', '')).lower()
    if hasattr(entry, 'content') and entry.content:
        text_to_search += " " + entry.content[0].value.lower()

    # ⚡ Bolt: Using a single compiled regex reduces search time significantly compared to looping over 21 individual regexes
    found_genres = {m.title() for m in GENRE_REGEX.findall(text_to_search)}
    genre = ", ".join(sorted(found_genres)) if found_genres else "Unknown/Other"

    title = getattr(entry, 'title', 'No Title')
    is_valid = True
    if 'link' in title.lower() and len(title) < 15:
        is_valid = False

    return {
        "title": title,
        "genre": genre,
        "is_valid": is_valid
    }

def extract_gemini_data(entry, gemini_client):
    if not gemini_client:
        return extract_fallback(entry)

    text_to_search = getattr(entry, 'title', '') + "\n" + getattr(entry, 'summary', '')
    if hasattr(entry, 'content') and entry.content:
        soup = BeautifulSoup(entry.content[0].value, 'html.parser')
        text_to_search += "\n" + soup.get_text()

    prompt = (
        "Review this Reddit post about an AI vertical drama or short drama. "
        "Analyze the title and content. "
        "1. Extract the clean, core title of the drama. Remove any Reddit tags (like [NSFW], (OC), etc.) or extraneous text like 'Does anyone know this one?'. "
        "2. Determine the most accurate genre trope (e.g., Mafia, CEO, Alpha, Werewolf, Billionaire, Romance, Revenge, Contract Marriage). If you cannot determine a genre, return 'Unknown/Other'. "
        "3. Determine if this post is a valid drama entry or just a meta-post/question (e.g. 'Link?', 'Help find this'). If it is just asking for a link or help and doesn't actually share a drama, mark it invalid.\n\n"
        "Return the result AS A VALID JSON OBJECT EXACTLY like this (do not include markdown codeblocks or any other text):\n"
        "{\n"
        '  "title": "Cleaned Drama Title",\n'
        '  "genre": "Mafia, Romance",\n'
        '  "is_valid": true\n'
        "}\n\n"
        f"Text:\n{text_to_search}"
    )

    try:
        response = gemini_client.models.generate_content(
            model='gemini-1.5-flash',
            contents=prompt,
        )
        result_text = response.text.strip()
        # Handle markdown blocks if present
        if result_text.startswith('```json'):
            result_text = result_text[7:]
        elif result_text.startswith('```'):
            result_text = result_text[3:]
        if result_text.endswith('```'):
            result_text = result_text[:-3]

        result_text = result_text.strip()

        data = json.loads(result_text)
        return {
            "title": data.get("title", getattr(entry, 'title', 'No Title')),
            "genre": data.get("genre", "Unknown/Other"),
            "is_valid": data.get("is_valid", True)
        }
    except Exception as e:
        print(f"Gemini extraction failed: {e}. Using fallback.")
        return extract_fallback(entry)


def sanitize_for_sheets(value):
    if isinstance(value, str) and value and value[0] in ('=', '+', '-', '@'):
        return "'" + value
    return value

def get_existing_data(client):
    if not client:
        return set(), set()
    try:
        sheet = client.open_by_key(SHEET_ID).sheet1
        # Use get_all_values to avoid issues with duplicate or missing headers
        records = sheet.get_all_values()
        if not records:
            return set(), set()

        headers = records[0]
        try:
            title_idx = headers.index('Title')
            source_link_idx = headers.index('Source Link')
        except ValueError:
            print("Warning: Could not find 'Title' or 'Source Link' columns in sheet. Duplicate checking may fail.")
            return set(), set()

        existing_titles = set()
        existing_source_links = set()

        for row in records[1:]:
            if len(row) > title_idx and row[title_idx]:
                existing_titles.add(row[title_idx].lower().strip())
            if len(row) > source_link_idx and row[source_link_idx]:
                existing_source_links.add(row[source_link_idx].lower().strip())

        return existing_titles, existing_source_links
    except Exception as e:
        print(f"Error fetching existing data from Google Sheets: {e}")
        return set(), set()

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
    client = get_google_sheets_client()
    existing_titles, existing_source_links = get_existing_data(client)

    gemini_client = get_gemini_client()
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
        source_link, watch_link = extract_links(entry)
        raw_title = getattr(entry, 'title', 'No Title')

        # Fast fail if source link is already in sheet
        if source_link.lower().strip() in existing_source_links:
            print(f"Skipping duplicate source link: {source_link}")
            continue

        gemini_data = extract_gemini_data(entry, gemini_client)
        if not gemini_data.get('is_valid', True):
            print(f"Skipping invalid entry: {raw_title}")
            continue

        title = gemini_data.get('title', 'No Title')

        # Check again using the cleaned title
        if title.lower().strip() in existing_titles:
            print(f"Skipping duplicate title: {title}")
            continue

        genre = gemini_data.get('genre', 'Unknown/Other')

        try:
            # Parse the published string if it exists to clean it up
            if hasattr(entry, 'published_parsed') and entry.published_parsed:
                date = time.strftime('%Y-%m-%d', entry.published_parsed)
            else:
                date = datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%d')
        except Exception:
            date = datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%d')

        # Headers: Title, Watch Link, Source Link, Link Status, Genre, Rating, Reactions & Notes, Date Added, Platform, Watch Status
        row = [
            title,           # A: Title
            watch_link,      # B: Watch Link
            source_link,     # C: Source Link
            'Searching / Requesting' if not watch_link else 'Ready to Watch', # D: Link Status
            genre,           # E: Genre
            '',              # F: Rating
            '',              # G: Reactions & Notes
            date,            # H: Date Added
            'Reddit',        # I: Platform
            'Plan to Watch'  # J: Watch Status
        ]
        rows_to_append.append(row)

        print(f"Scraped: {title} | {source_link} | {watch_link} | {genre} | {date}")

    client = get_google_sheets_client()
    if client:
        append_to_sheet(client, rows_to_append)
    else:
        print("Skipping Google Sheets append because client could not be initialized.")

if __name__ == '__main__':
    main()
