import tracemalloc
import sys

class Tag:
    def __init__(self, term):
        self.term = term

class Entry:
    def __init__(self, tags):
        self.tags = tags

def extract_genre_original(entry):
    if hasattr(entry, 'tags'):
        tags = [tag.term for tag in entry.tags]
        if tags:
            return ", ".join(tags)
    return "N/A"

def extract_genre_optimized(entry):
    if hasattr(entry, 'tags') and entry.tags:
        return ", ".join(tag.term for tag in entry.tags)
    return "N/A"

# Test with many tags
entry = Entry([Tag(f"tag{i}") for i in range(1000000)])

tracemalloc.start()
extract_genre_original(entry)
current, peak = tracemalloc.get_traced_memory()
tracemalloc.stop()
print(f"Original Peak Memory: {peak / 10**6} MB")

tracemalloc.start()
extract_genre_optimized(entry)
current, peak = tracemalloc.get_traced_memory()
tracemalloc.stop()
print(f"Optimized Peak Memory: {peak / 10**6} MB")
