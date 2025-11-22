#!/usr/bin/env python
"""
Test CSRF token extraction and proper POST submission
"""
import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'evaluationWeb.settings')
django.setup()

from django.test import Client
import re

print("="*80)
print("CSRF TOKEN EXTRACTION TEST")
print("="*80)

# Step 1: Get login page and extract CSRF token
client = Client(enforce_csrf_checks=True)
print("\n[1] GET /login/ to extract CSRF token from HTML...")
response = client.get('/login/')
print(f"    Status: {response.status_code}")

# Extract CSRF token from HTML
html_content = response.content.decode('utf-8')
match = re.search(r'name=["\']csrfmiddlewaretoken["\'][^>]+value=["\']([^"\']+)["\']', html_content)

if match:
    csrf_token = match.group(1)
    print(f"    ✅ CSRF token extracted from HTML: {csrf_token[:30]}...")
else:
    print(f"    ❌ CSRF token NOT found in HTML")
    # Print part of the form to debug
    form_match = re.search(r'<form[^>]*>.*?</form>', html_content, re.DOTALL)
    if form_match:
        form_section = form_match.group(0)[:500]
        print(f"    Form section: {form_section}")
    sys.exit(1)

# Step 2: Try POST with explicit CSRF token in data
print(f"\n[2] POST /login/ with CSRF token explicitly in POST data...")
test_data = {
    'email': 'Christianbituonon4@gmail.com',
    'password': 'VNxv76dBIbL@JO7UDqLo',
    'csrfmiddlewaretoken': csrf_token,  # Explicitly add CSRF token
}

try:
    response = client.post('/login/', test_data)
    print(f"    Status: {response.status_code}")
    
    if response.status_code == 302:
        print(f"    ✅ ✅ ✅ SUCCESS! Got 302 redirect")
        print(f"    Redirects to: {response.url}")
    elif response.status_code == 403:
        print(f"    ❌ FORBIDDEN - CSRF still failing")
    elif response.status_code == 200:
        print(f"    ⚠️  Got 200 (form not accepted)")
        if b'Incorrect Username or Password' in response.content:
            print(f"    Message: 'Incorrect Username or Password' shown")
    else:
        print(f"    Status: {response.status_code}")
        
except Exception as e:
    print(f"    ❌ ERROR: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "="*80)
