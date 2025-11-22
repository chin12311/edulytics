#!/usr/bin/env python
"""
Test CSRF token handling in login form
"""
import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'evaluationWeb.settings')
django.setup()

from django.test import Client
from django.middleware.csrf import get_token
from django.urls import reverse

print("="*80)
print("CSRF TOKEN TEST")
print("="*80)

client = Client()

# Step 1: GET login page to get CSRF token
print("\n1. Getting login page...")
login_url = reverse('register:login')
response = client.get(login_url)
print(f"   Status: {response.status_code}")
print(f"   Content-Type: {response.get('Content-Type')}")

# Check if CSRF token is in the form
csrf_token = response.context.get('csrf_token') if response.context else None
print(f"   CSRF token in context: {'YES' if csrf_token else 'NO'}")

# Look for csrf token in the HTML
if b'csrfmiddlewaretoken' in response.content:
    print(f"   CSRF token in HTML: YES")
else:
    print(f"   CSRF token in HTML: NO ⚠️")

# Step 2: Try login WITH CSRF token
print("\n2. Testing login WITH CSRF token handling...")
client2 = Client(enforce_csrf_checks=True)
response = client2.get(login_url)
csrf_from_cookie = response.cookies.get('csrftoken')
print(f"   CSRF cookie from GET: {csrf_from_cookie.value if csrf_from_cookie else 'MISSING'}")

# Try POST with CSRF
try:
    response = client2.post(
        login_url,
        data={
            'email': 'Christianbituonon4@gmail.com',
            'password': 'VNxv76dBIbL@JO7UDqLo',
        },
        follow=False
    )
    print(f"   POST response status: {response.status_code}")
    print(f"   Response content (first 200 chars): {response.content[:200]}")
except Exception as e:
    print(f"   Error during POST: {e}")

# Step 3: Check CSRF settings
print("\n3. CSRF Configuration:")
from django.conf import settings
print(f"   CSRF_TRUSTED_ORIGINS: {settings.CSRF_TRUSTED_ORIGINS}")
print(f"   CSRF_COOKIE_SECURE: {settings.CSRF_COOKIE_SECURE}")
print(f"   CSRF_COOKIE_HTTPONLY: {settings.CSRF_COOKIE_HTTPONLY}")
print(f"   CSRF_COOKIE_SAMESITE: {settings.CSRF_COOKIE_SAMESITE}")
print(f"   SESSION_COOKIE_SECURE: {settings.SESSION_COOKIE_SECURE}")
print(f"   SESSION_COOKIE_HTTPONLY: {settings.SESSION_COOKIE_HTTPONLY}")
print(f"   SESSION_COOKIE_SAMESITE: {settings.SESSION_COOKIE_SAMESITE}")

print("\n" + "="*80)
