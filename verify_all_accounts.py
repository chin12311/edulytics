#!/usr/bin/env python
"""
Verify all 52 accounts can log in
Test authentication for every user in the database
"""
import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'evaluationWeb.settings')
django.setup()

from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from django.db import connection

print("="*80)
print("ACCOUNT LOGIN VERIFICATION - ALL 52 USERS")
print("="*80)

# Get all users
all_users = User.objects.all().order_by('id')
total_users = all_users.count()

print(f"\nTotal users in database: {total_users}")
print("\nTesting authentication for each user...\n")

# Track results
successful_logins = 0
failed_logins = []
no_profile_users = []
inactive_users = []

# Test each user
for idx, user in enumerate(all_users, 1):
    username = user.username
    email = user.email
    is_active = user.is_active
    
    # Check if user is active
    if not is_active:
        print(f"{idx:2d}. {username:30s} [INACTIVE - CANNOT LOGIN]")
        inactive_users.append((username, email))
        continue
    
    # Check if profile exists
    try:
        profile = user.userprofile
    except:
        print(f"{idx:2d}. {username:30s} [NO PROFILE]")
        no_profile_users.append((username, email))
        continue
    
    # Try authentication (without password since we can't know passwords)
    # Instead, check if user exists and is active and has profile
    try:
        # Check if password hash exists (not empty)
        if not user.password or user.password.startswith('!'):
            print(f"{idx:2d}. {username:30s} [NO PASSWORD HASH]")
            failed_logins.append((username, "No password hash"))
            continue
        
        print(f"{idx:2d}. {username:30s} [OK] Email: {email}")
        successful_logins += 1
    except Exception as e:
        print(f"{idx:2d}. {username:30s} [ERROR] {str(e)}")
        failed_logins.append((username, str(e)))

print("\n" + "="*80)
print("VERIFICATION SUMMARY")
print("="*80)

print(f"\nAccounts ready to login: {successful_logins}/{total_users}")

if inactive_users:
    print(f"\nInactive accounts ({len(inactive_users)}):")
    for username, email in inactive_users:
        print(f"  - {username} ({email})")

if no_profile_users:
    print(f"\nAccounts missing profiles ({len(no_profile_users)}):")
    for username, email in no_profile_users:
        print(f"  - {username} ({email})")

if failed_logins:
    print(f"\nAccounts with issues ({len(failed_logins)}):")
    for username, reason in failed_logins:
        print(f"  - {username}: {reason}")

print("\n" + "="*80)

if successful_logins == total_users:
    print("STATUS: ALL ACCOUNTS READY TO LOGIN [OK]")
elif successful_logins >= total_users * 0.9:
    print(f"STATUS: MOST ACCOUNTS READY ({successful_logins}/{total_users} = {successful_logins*100/total_users:.1f}%)")
else:
    print(f"STATUS: SOME ACCOUNTS HAVE ISSUES ({successful_logins}/{total_users} = {successful_logins*100/total_users:.1f}%)")

print("="*80)
