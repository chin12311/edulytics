#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'evaluationWeb.settings')
django.setup()

from django.core.cache import cache

print("=" * 60)
print("CHECKING AND CLEARING RATE LIMITS")
print("=" * 60)

print("\n1. Checking cache for rate limit entries...")
cache_keys = cache.keys("rate_limit:*")
print(f"   Found {len(cache_keys)} rate limit entries:")
for key in cache_keys:
    value = cache.get(key)
    print(f"   - {key}: {value} attempts")

if cache_keys:
    print("\n2. Clearing all rate limits...")
    for key in cache_keys:
        cache.delete(key)
    print("   ✓ All rate limits cleared!")
    
    # Verify they're gone
    cache_keys_after = cache.keys("rate_limit:*")
    print(f"   Verification: {len(cache_keys_after)} rate limit entries remaining")
else:
    print("\n   No rate limits found - user can try login again")

print("\n" + "=" * 60)
print("Cache status after cleanup:")
print("=" * 60)

# Show overall cache info if possible
try:
    cache_info = cache.keys("*")
    print(f"Total cache entries: {len(cache_info)}")
    print("First 10 entries:")
    for key in cache_info[:10]:
        print(f"  - {key}")
except Exception as e:
    print(f"Could not get full cache info: {e}")

print("\n" + "=" * 60)
