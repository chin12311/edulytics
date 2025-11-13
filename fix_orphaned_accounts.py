#!/usr/bin/env python
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'evaluationWeb.settings')
sys.path.insert(0, r'c:\Users\ADMIN\eval\evaluation')
django.setup()

from django.contrib.auth.models import User
from main.models import UserProfile, Role
import logging

logger = logging.getLogger(__name__)

print("=" * 80)
print("FIXING ORPHANED ACCOUNTS")
print("=" * 80)

# Find users without profiles
users_without_profile = User.objects.filter(userprofile__isnull=True)
count = users_without_profile.count()
print(f"\n Found {count} orphaned users")

if count == 0:
    print("✅ No orphaned accounts found!")
else:
    print(f"\nFixing {count} orphaned accounts...\n")
    
    created_count = 0
    failed = []
    
    for user in users_without_profile:
        try:
            profile = UserProfile(
                user=user,
                role=Role.ADMIN,  # Temp role - no constraints
                display_name=user.get_full_name() or user.username
            )
            profile.save(skip_validation=True)
            created_count += 1
            print(f"  ✅ Fixed: {user.username} ({user.email})")
        except Exception as e:
            failed.append((user.username, str(e)))
            print(f"  ❌ Failed: {user.username} - {str(e)}")
    
    print(f"\n{'='*80}")
    print(f"SUMMARY:")
    print(f"  Total orphaned: {count}")
    print(f"  Fixed: {created_count}")
    print(f"  Failed: {len(failed)}")
    
    if failed:
        print(f"\nFailed accounts:")
        for username, error in failed:
            print(f"  - {username}: {error}")
    else:
        print(f"\n✅ ALL ORPHANED ACCOUNTS FIXED!")

# Verify
print(f"\n{'='*80}")
print("VERIFICATION:")
remaining = User.objects.filter(userprofile__isnull=True).count()
print(f"  Orphaned accounts remaining: {remaining}")

if remaining == 0:
    print(f"\n✅ SUCCESS - All users now have profiles!")
else:
    print(f"\n❌ {remaining} accounts still need fixing")

print(f"{'='*80}\n")
