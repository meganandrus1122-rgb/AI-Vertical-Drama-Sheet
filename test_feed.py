import feedparser
d = feedparser.parse('https://www.reddit.com/r/shortdrama/search.rss?q=AI&sort=new')
print(d.entries[0] if len(d.entries) > 0 else "No entries")
