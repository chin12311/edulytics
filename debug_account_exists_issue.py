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

print("=" * 80)
print("INVESTIGATING 'ACCOUNT ALREADY EXISTS' ISSUE")
print("=" * 80)

# Test email
test_email = input("\nEnter email to check: ").strip().lower()

print(f"\nChecking for email: {test_email}")
print("-" * 80)

# Check if User exists
user_exists = User.objects.filter(email__iexact=test_email).exists()
print(f"User with this email: {user_exists}")

if user_exists:
    user = User.objects.get(email__iexact=test_email)
    print(f"  Username: {user.username}")
    print(f"  Date joined: {user.date_joined}")
    
    try:
        profile = user.userprofile
        print(f"  Profile exists: YES")
        print(f"    Profile ID: {profile.id}")
        print(f"    Role: {profile.role}")
        print(f"    Display Name: {profile.display_name}")
    except UserProfile.DoesNotExist:
        print(f"  Profile exists: NO (orphaned user!)")

# Check if UserProfile with this email exists (shouldn't be a field, but let's check)
print(f"\nChecking UserProfile table for any association...")
profiles = UserProfile.objects.filter(user__email__iexact=test_email)
print(f"Profiles matching this email: {profiles.count()}")

# Check username generated from email
username_base = test_email.split('@')[0]
username_clean = ''.join(c for c in username_base if c.isalnum()).lower()

print(f"\nGenerated username from email: {username_clean}")
print("-" * 80)

# Check if this username exists
user_exists_by_username = User.objects.filter(username=username_clean).exists()
print(f"User with username '{username_clean}': {user_exists_by_username}")

# Check all similar usernames
print(f"\nChecking for similar usernames (collision check):")
similar = User.objects.filter(username__startswith=username_clean)
for u in similar:
    print(f"  - {u.username} ({u.email})")

# Show what would happen on a fresh registration
print(f"\n" + "=" * 80)
print("FRESH REGISTRATION CHECK")
print("=" * 80)

print(f"\nIf you try to register with {test_email}:")
if User.objects.filter(email__iexact=test_email).exists():
    print(f"  ❌ Would fail: 'A user with this email already exists.'")
    print(f"  Reason: Email already in User table")
else:
    print(f"  ✅ Email check would PASS")
    
    # Check username
    username = username_clean
    counter = 1
    while User.objects.filter(username=username).exists():
        username = f"{username_clean}{counter}"
        counter += 1
    
    print(f"  ✅ Username check would PASS")
    print(f"  Generated username: {username}")

print("\n" + "=" * 80)
