#!/usr/bin/env python
"""
Simple test: Which database is being used and are all 52 accounts ready?
"""
import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'evaluationWeb.settings')
django.setup()

from django.contrib.auth.models import User
from django.db import connection, connections
from django.conf import settings

print("="*80)
print("DATABASE & ACCOUNT STATUS")
print("="*80)

# Get database connection info
conn = connections['default']
db_config = conn.get_connection_params()

print("\n[DATABASE CONNECTION]")
print(f"  Host: {db_config.get('host', 'unknown')}")
print(f"  Database: {db_config.get('db', 'unknown')}")
print(f"  User: {db_config.get('user', 'unknown')}")
print(f"  Engine: {connection.vendor}")

# Get user count
user_count = User.objects.count()
active_count = User.objects.filter(is_active=True).count()
inactive_count = User.objects.filter(is_active=False).count()

print(f"\n[USERS IN DATABASE]")
print(f"  Total users: {user_count}")
print(f"  Active users: {active_count}")
print(f"  Inactive users: {inactive_count}")

# Check profiles
from main.models import UserProfile

profile_count = UserProfile.objects.count()
print(f"\n[USER PROFILES]")
print(f"  Total profiles: {profile_count}")

# Status
print(f"\n[STATUS]")
if user_count == 52 and active_count == 52 and profile_count == 52:
    print("  [OK] ALL 52 ACCOUNTS READY TO LOGIN")
    print("  ✓ Database: CONFIGURED")
    print("  ✓ Users: 52/52 present")
    print("  ✓ Profiles: 52/52 present")
    print("  ✓ Active: All 52 active")
    print("\n  RESULT: System ready for production use!")
else:
    print(f"  [WARNING] Some issues detected:")
    if user_count != 52:
        print(f"    - Users: {user_count} instead of 52")
    if active_count != 52:
        print(f"    - Active: {active_count} instead of 52")
    if profile_count != 52:
        print(f"    - Profiles: {profile_count} instead of 52")

print("\n" + "="*80)
