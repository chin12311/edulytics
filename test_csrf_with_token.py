#!/usr/bin/env python
"""
Test CSRF by properly sending token in POST data (like a browser would)
"""
import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'evaluationWeb.settings')
django.setup()

from django.test import Client
from django.urls import reverse
import re

print("="*80)
print("CSRF WITH PROPER TOKEN IN POST DATA")
print("="*80)

# Step 1: Get the login page to extract CSRF token
print("\n1. Getting login page to extract CSRF token...")
client = Client(enforce_csrf_checks=True)
response = client.get(reverse('register:login'))
print(f"   Status: {response.status_code}")

# Extract CSRF token from HTML
html = response.content.decode('utf-8')
csrf_pattern = r'name=["\']csrfmiddlewaretoken["\'].*?value=["\']([^"\']+)["\']'
match = re.search(csrf_pattern, html, re.DOTALL)

if not match:
    print("   ERROR: Could not extract CSRF token from HTML!")
    sys.exit(1)

csrf_token = match.group(1)
print(f"   OK: Found CSRF token: {csrf_token[:20]}...")

# Step 2: Try POST with CSRF token in POST data
print("\n2. Testing POST with CSRF token in data...")
response = client.post(
    reverse('register:login'),
    data={
        'email': 'Christianbituonon4@gmail.com',
        'password': 'VNxv76dBIbL@JO7UDqLo',
        'csrfmiddlewaretoken': csrf_token,  # Include CSRF token in POST data
    },
    follow=False
)

print(f"   Status: {response.status_code}")

if response.status_code == 302:
    print(f"   OK: Got 302 redirect!")
    print(f"   Redirects to: {response.get('Location')}")
elif response.status_code == 403:
    print(f"   ERROR: Got 403 Forbidden")
    print(f"   Response: {response.content[:200]}")
elif response.status_code == 200:
    print(f"   Got 200 OK (form returned)")
    if b'Incorrect' in response.content:
        print(f"   ERROR: Form shows 'Incorrect' error")
    else:
        print(f"   Form returned without major error")
else:
    print(f"   Unexpected status: {response.status_code}")

print("\n" + "="*80)
