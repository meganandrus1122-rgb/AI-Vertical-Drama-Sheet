import timeit
import time

class Tag:
    def __init__(self, term):
        self.term = term

class Entry:
    def __init__(self, tags):
        self.tags = tags

def extract_genre_original(entry):
    # Try to extract genre from tags/categories if present
    if hasattr(entry, 'tags'):
        tags = [tag.term for tag in entry.tags]
        if tags:
            return ", ".join(tags)
    return "N/A"

def extract_genre_optimized(entry):
    # Try to extract genre from tags/categories if present
    if hasattr(entry, 'tags') and entry.tags:
        return ", ".join(tag.term for tag in entry.tags)
    return "N/A"

entries = [Entry([Tag(f"tag{i}") for i in range(10)]) for _ in range(1000)]
empty_entries = [Entry([]) for _ in range(1000)]
no_tags_entries = [type('Entry', (), {})() for _ in range(1000)]

def run_bench(func, data):
    for entry in data:
        func(entry)

print("Original (10 tags):", timeit.timeit(lambda: run_bench(extract_genre_original, entries), number=10000))
print("Optimized (10 tags):", timeit.timeit(lambda: run_bench(extract_genre_optimized, entries), number=10000))

print("Original (0 tags):", timeit.timeit(lambda: run_bench(extract_genre_original, empty_entries), number=10000))
print("Optimized (0 tags):", timeit.timeit(lambda: run_bench(extract_genre_optimized, empty_entries), number=10000))

print("Original (no tags):", timeit.timeit(lambda: run_bench(extract_genre_original, no_tags_entries), number=10000))
print("Optimized (no tags):", timeit.timeit(lambda: run_bench(extract_genre_optimized, no_tags_entries), number=10000))
