#!/usr/bin/env python
import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'evaluationWeb.settings')
django.setup()

from django.core.cache import cache
from django.db import connection

print("="*80)
print("CHECKING RATE LIMIT CACHE")
print("="*80)

try:
    with connection.cursor() as cursor:
        cursor.execute("SELECT cache_key, cache_data FROM django_cache WHERE cache_key LIKE '%rate_limit%'")
        rows = cursor.fetchall()
    
    if rows:
        print("\nRATELIMIT CACHE ENTRIES FOUND:")
        for key, data in rows:
            print(f"\nKey: {key}")
            print(f"Data: {data[:50]}...")
    else:
        print("\n✅ NO RATE LIMIT ENTRIES IN CACHE")
        print("✅ User is NOT being rate-limited")
        
except Exception as e:
    print(f"Error checking cache: {e}")
    
    # Try alternate approach
    print("\nTrying alternate check...")
    for ip in ['127.0.0.1', 'localhost', '::1']:
        key = f'rate_limit:login_view:{ip}'
        result = cache.get(key)
        if result:
            print(f"⚠️  Rate limit entry for {ip}: {result} attempts")
        else:
            print(f"✅ No rate limit entry for {ip}")

print("\n" + "="*80)
