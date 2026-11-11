
## 2024-11-11 - [BeautifulSoup Overhead for Simple Extractions]
**Learning:** Using `BeautifulSoup` to parse entire HTML strings just to extract simple attributes (like a single `href`) is incredibly slow and memory intensive, adding massive overhead (e.g. ~180x slower than regex).
**Action:** For simple, targeted extractions like a single HTML attribute, prioritize pre-compiled regex over full DOM parsers like `BeautifulSoup`. Always decode entities with `html.unescape` when using regex to ensure correctness parity with full parsers.
