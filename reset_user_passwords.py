#!/usr/bin/env python
"""Reset non-admin user passwords to a default password so they can log in."""

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'evaluationWeb.settings')
django.setup()

from django.contrib.auth.models import User
from django.contrib.auth import authenticate

DEFAULT_PASSWORD = 'EduLytics@2025'
ADMIN_ACCOUNTS = ['Admin', 'Christian Bitu-onon1']

all_users = User.objects.all()
admin_users = all_users.filter(username__in=ADMIN_ACCOUNTS)
regular_users = all_users.exclude(username__in=ADMIN_ACCOUNTS)

print("=" * 80)
print("RESETTING USER PASSWORDS")
print("=" * 80)
print(f"\n📋 Plan:")
print(f"   • Keep admin accounts unchanged: {ADMIN_ACCOUNTS}")
print(f"   • Reset {regular_users.count()} regular users to: {DEFAULT_PASSWORD}\n")

count = 0
print(f"🔄 Resetting passwords...")
print("-" * 80)

for user in regular_users.order_by('username'):
    user.set_password(DEFAULT_PASSWORD)
    user.save()
    count += 1
    if count <= 10 or count % 10 == 0:
        print(f"✅ {user.username:40s}")

print("-" * 80)
print(f"\n✅ Successfully reset {count} user passwords!")

# Verify
print(f"\n🧪 Verifying with test logins...")
print("-" * 80)

test_cases = [
    ('Christian Bitu-onon1', 'VNxv76dBIbL@JO7UDqLo'),
    ('Admin', 'VNxv76dBIbL@JO7UDqLo'),
    ('aerondavecaligagan1', 'EduLytics@2025'),
    ('clydelubat', 'EduLytics@2025'),
]

for username, password in test_cases:
    auth_result = authenticate(username=username, password=password)
    status = "✅" if auth_result else "❌"
    print(f"{status} {username:40s} - {password}")

print("-" * 80)
print(f"\n📝 LOGIN INSTRUCTIONS:")
print(f"   Admin account (unchanged):")
print(f"      Email: Christianbituonon4@gmail.com")
print(f"      Password: VNxv76dBIbL@JO7UDqLo")
print(f"\n   All other {regular_users.count()} accounts:")
print(f"      Email: [their registered email]")
print(f"      Password: {DEFAULT_PASSWORD}")
print("\n" + "=" * 80)
