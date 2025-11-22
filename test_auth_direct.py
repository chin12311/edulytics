#!/usr/bin/env python
"""
Direct authentication test - no HTTP layer
"""
import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'evaluationWeb.settings')
django.setup()

from django.contrib.auth.models import User
from django.contrib.auth import authenticate

print("="*80)
print("DIRECT AUTHENTICATION TEST")
print("="*80)

# Get first user
user = User.objects.first()

if not user:
    print("\n❌ No users in database!")
    sys.exit(1)

print(f"\nUser: {user.username}")
print(f"Email: {user.email}")
print(f"Active: {user.is_active}")
print(f"Password hash: {user.password[:50]}...")

# Test 1: Check password directly
print(f"\n[TEST 1] Direct password check")
test_passwords = [
    "VNxv76dBIbL@JO7UDqLo",  # Known admin password
    "Admin@123",             # Common password
    "EduLytics@2025",        # Default password
    "password",              # Random
]

for pwd in test_passwords:
    result = user.check_password(pwd)
    print(f"  check_password('{pwd[:10]}...'): {result}")

# Test 2: Authenticate with username
print(f"\n[TEST 2] Authenticate with username")
for pwd in test_passwords:
    result = authenticate(username=user.username, password=pwd)
    print(f"  authenticate(username, password='{pwd[:10]}...'): {result}")

# Test 3: Authenticate with email (if it works)
print(f"\n[TEST 3] Authenticate with email (might not work)")
for pwd in test_passwords:
    try:
        result = authenticate(username=user.email, password=pwd)
        print(f"  authenticate(email, password='{pwd[:10]}...'): {result}")
    except Exception as e:
        print(f"  authenticate(email, password='{pwd[:10]}...'): ERROR - {e}")

print("\n" + "="*80)
