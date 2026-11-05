## 2024-11-20 - Fast fallback keyword extraction
**Learning:** Checking for 21 genre keywords using 21 separate compiled regexes in a loop is significantly slower than building a single combined compiled regex with alternation.
**Action:** Use single compiled regexes using `r'\b(' + '|'.join(re.escape(k) for k in keywords) + r')\b'` and `.findall()` over looping when doing keyword checks against a string.
