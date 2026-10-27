import timeit
import datetime

class DummyEntry:
    pass

entries = [DummyEntry() for _ in range(100000)]

def run_unoptimized():
    rows_to_append = []
    for entry in entries:
        date = entry.published if hasattr(entry, 'published') else datetime.datetime.utcnow().isoformat()
        rows_to_append.append(date)

def run_optimized():
    rows_to_append = []
    fallback_date = datetime.datetime.utcnow().isoformat()
    for entry in entries:
        date = entry.published if hasattr(entry, 'published') else fallback_date
        rows_to_append.append(date)

print("Unoptimized:", timeit.timeit(run_unoptimized, number=10))
print("Optimized:", timeit.timeit(run_optimized, number=10))
