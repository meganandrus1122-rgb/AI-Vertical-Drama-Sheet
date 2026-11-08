
## 2024-05-18 - Replacing BeautifulSoup with regex for simple HTML extractions
**Learning:** Using full DOM parsing libraries like `BeautifulSoup` solely to extract simple elements (like the first `href` from `<a>` tags) creates significant performance bottlenecks, especially when repeated across many entries in a feed or loop, because it introduces O(N) DOM parsing overhead for O(1) targeted extraction.
**Action:** Always prefer a pre-compiled regular expression over full DOM parsing libraries (like `BeautifulSoup` or `lxml`) for straightforward, targeted HTML scraping (e.g., retrieving a single attribute from a tag) to minimize performance overhead.
