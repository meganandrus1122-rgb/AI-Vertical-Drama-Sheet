## 2025-02-09 - Regex Tag Extraction
**Learning:** When using regular expressions for targeted HTML element extraction, ensure proper boundaries or spaces are used (e.g., `<a\s+` instead of `<a`) to prevent false positive matches with similarly prefixed tags (like `<article`).
**Action:** Always include boundary checks like `\s+` or `\b` when using regex to extract specific HTML tags to avoid accidentally matching unrelated tags that share a prefix.
