#!/usr/bin/env python
"""
Test if CSRF failures are due to cookies not being set/sent
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
print("CSRF COOKIE HANDLING TEST")
print("="*80)

# Test 1: Get page and check for CSRF cookies
print("\n1. Getting login page...")
client = Client(enforce_csrf_checks=True)
response = client.get(reverse('register:login'))

print(f"   Status: {response.status_code}")
print(f"   Cookies: {list(response.cookies.keys())}")

csrf_cookie = response.cookies.get('csrftoken')
if csrf_cookie:
    print(f"   CSRF cookie set: YES")
    print(f"   Cookie value: {csrf_cookie.value[:20]}...")
else:
    print(f"   CSRF cookie set: NO")

# Test 2: Extract CSRF token from HTML
html = response.content.decode('utf-8')
csrf_pattern = r'name=["\']csrfmiddlewaretoken["\'].*?value=["\']([^"\']+)["\']'
match = re.search(csrf_pattern, html, re.DOTALL)

if match:
    csrf_token = match.group(1)
    print(f"   CSRF token in HTML: YES ({csrf_token[:20]}...)")
else:
    print(f"   CSRF token in HTML: NO")

# Test 3: POST without any CSRF (should fail)
print("\n2. Testing POST without CSRF token...")
response = client.post(
    reverse('register:login'),
    data={'email': 'test@test.com', 'password': 'test'},
    follow=False
)
print(f"   Status: {response.status_code}")
if response.status_code == 403:
    print(f"   OK: Got 403 Forbidden (expected for no CSRF)")
elif response.status_code == 200:
    print(f"   Got 200 OK - might indicate CSRF check is weak")
else:
    print(f"   Got {response.status_code}")

# Test 4: POST with only cookie CSRF (no POST data CSRF)
print("\n3. Testing POST with CSRF cookie only (no POST data)...")
# The client should automatically use the cookie
response = client.post(
    reverse('register:login'),
    data={'email': 'test@test.com', 'password': 'test'},
    follow=False,
    # Not including csrfmiddlewaretoken in POST data
)
print(f"   Status: {response.status_code}")
if response.status_code == 403:
    print(f"   Got 403 - CSRF cookie alone not sufficient")
elif response.status_code == 200:
    print(f"   Got 200 - CSRF might be working")
else:
    print(f"   Got {response.status_code}")

# Test 5: Manually set cookies
print("\n4. Testing POST with manually set CSRF cookie...")
# Get fresh page
response1 = client.get(reverse('register:login'))
csrf_value = None

# Extract from HTML
html = response1.content.decode('utf-8')
match = re.search(csrf_pattern, html, re.DOTALL)
if match:
    csrf_value = match.group(1)
    print(f"   Extracted CSRF token: {csrf_value[:20]}...")

# Now POST with CSRF in data
response2 = client.post(
    reverse('register:login'),
    data={
        'email': 'Christianbituonon4@gmail.com',
        'password': 'VNxv76dBIbL@JO7UDqLo',
        'csrfmiddlewaretoken': csrf_value,
    },
    follow=False
)

print(f"   POST Status: {response2.status_code}")
if response2.status_code == 302:
    print(f"   OK: Got 302 redirect - LOGIN SUCCESS!")
elif response2.status_code == 403:
    print(f"   Got 403 - CSRF check failed even with token in POST data")
elif response2.status_code == 200:
    print(f"   Got 200 - Form returned")
    if b'Incorrect' in response2.content:
        print(f"   ERROR: Form shows 'Incorrect' message")

print("\n" + "="*80)
