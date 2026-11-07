## 2024-05-24 - HTML Parsing vs Regex for Single Attributes
**Learning:** Using `BeautifulSoup` to parse entire RSS HTML entries just to extract a single `href` from an anchor tag incurs massive, unnecessary overhead. In benchmarks, targeted regex extraction (`re.compile` with `re.finditer`) is ~200x faster than full DOM parsing.
**Action:** When extracting a specific attribute or substring from simple HTML structures (especially frequently processed payloads like RSS entries), prefer pre-compiled Regex over heavy libraries like `BeautifulSoup` if complex DOM traversal isn't required.
