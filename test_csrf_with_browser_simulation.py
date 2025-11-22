#!/usr/bin/env python
"""
Test CSRF handling - simulates what a real browser does with cookies
"""
import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'evaluationWeb.settings')
django.setup()

from django.test import Client
import re

print("="*80)
print("CSRF TOKEN TEST - Browser Simulation with Cookies")
print("="*80)

# Create a client with CSRF checks enabled (simulates real browser)
client = Client(enforce_csrf_checks=True)

print("\n[1] GET /login/ to get CSRF token...")
response = client.get('/login/')
print(f"   Status: {response.status_code}")

# Extract CSRF token from HTML
csrf_token = None
if 'csrftoken' in response.cookies:
    csrf_token = response.cookies['csrftoken'].value
    print(f"   ✅ CSRF cookie found: {csrf_token[:20]}...")
else:
    print(f"   ⚠️  No CSRF cookie in response")
    
# Also try to extract from HTML
html_content = response.content.decode('utf-8')
match = re.search(r'<input[^>]+name=["\']csrfmiddlewaretoken["\'][^>]+value=["\']([^"\']+)["\']', html_content)
if match:
    html_csrf_token = match.group(1)
    print(f"   ✅ CSRF token in HTML: {html_csrf_token[:20]}...")
else:
    print(f"   ⚠️  No CSRF token in HTML")

print("\n[2] POST /login/ with credentials and CSRF token...")

# Try login with the CSRF token from cookies
test_data = {
    'email': 'Christianbituonon4@gmail.com',
    'password': 'VNxv76dBIbL@JO7UDqLo',
}

try:
    response = client.post('/login/', test_data)
    print(f"   Status: {response.status_code}")
    
    if response.status_code == 302:
        print(f"   ✅ ✅ ✅ REDIRECT (302) - LOGIN SUCCESSFUL!")
        print(f"   Redirects to: {response.url}")
    elif response.status_code == 403:
        print(f"   ❌ FORBIDDEN (403) - CSRF TOKEN ISSUE")
        if b'CSRF token missing' in response.content:
            print(f"   Error: CSRF token missing")
        if b'CSRF token incorrect' in response.content:
            print(f"   Error: CSRF token incorrect")
    elif response.status_code == 200:
        print(f"   ⚠️  200 OK (NOT REDIRECT) - Form not accepted")
        if b'Incorrect Username or Password' in response.content:
            print(f"   Error: 'Incorrect Username or Password' message shown")
    else:
        print(f"   Status: {response.status_code}")
        
except Exception as e:
    print(f"   ❌ ERROR: {e}")

print("\n" + "="*80)
print("SUMMARY:")
print("  If you see 302: Browser form submission should work")
print("  If you see 403: CSRF token not being sent properly")
print("  If you see 200 + error message: Credentials issue (but unlikely)")
print("="*80)
