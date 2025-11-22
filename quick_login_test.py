#!/usr/bin/env python
"""
Quick test - Run this while Django server is running to verify login works
"""
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'evaluationWeb.settings')

import django
django.setup()

from django.test import Client
from django.urls import reverse
from django.contrib.auth.models import User

print("=" * 80)
print("QUICK LOGIN TEST - Run this while server is running")
print("=" * 80)

# Get the user
try:
    user = User.objects.get(email__iexact='Christianbituonon4@gmail.com')
    print(f"\n✅ User found: {user.username}")
    print(f"   Email: {user.email}")
    print(f"   Password valid: {user.check_password('VNxv76dBIbL@JO7UDqLo')}")
except User.DoesNotExist:
    print(f"\n❌ User not found!")
    exit(1)

# Test HTTP login
client = Client()
response = client.post(
    reverse('register:login'),
    {'email': 'Christianbituonon4@gmail.com', 'password': 'VNxv76dBIbL@JO7UDqLo'},
    follow=False
)

print(f"\n📝 HTTP Login Test Result:")
print(f"   Status Code: {response.status_code}")

if response.status_code == 302:
    print(f"   ✅ ✅ ✅ REDIRECT RECEIVED - LOGIN WORKS! ✅ ✅ ✅")
    print(f"   Redirects to: {response.get('Location')}")
elif response.status_code == 200:
    print(f"   ⚠️ Still on login page (200 OK)")
    if 'Invalid email' in response.content.decode():
        print(f"   ❌ ERROR: Invalid email or password message present")
    else:
        print(f"   ℹ️ Form returned without obvious errors")
else:
    print(f"   ❌ Unexpected status: {response.status_code}")

print("\n" + "=" * 80)
