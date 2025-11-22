#!/usr/bin/env python
"""
Test: Does TestClient.post() automatically include CSRF token from form HTML?
"""
import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'evaluationWeb.settings')
django.setup()

from django.test import Client
import re

print("="*80)
print("AUTO CSRF TOKEN TEST")
print("="*80)

# Method 1: WITHOUT enforce_csrf_checks (simulates unsafe browser)
print("\n[METHOD 1] Client without enforce_csrf_checks:")
print("-" * 80)
client = Client()
response = client.get('/login/')
response = client.post('/login/', {
    'email': 'Christianbituonon4@gmail.com',
    'password': 'VNxv76dBIbL@JO7UDqLo',
})
print(f"Status: {response.status_code}")
if response.status_code == 302:
    print("✅ Works without CSRF checks")
elif response.status_code == 200:
    print("❌ Returns 200 (form error shown)")
else:
    print(f"Status: {response.status_code}")

# Method 2: WITH enforce_csrf_checks (simulates real browser)
print("\n[METHOD 2] Client with enforce_csrf_checks=True:")
print("-" * 80)
client_strict = Client(enforce_csrf_checks=True)
response = client_strict.get('/login/')

# Extract CSRF token manually
html = response.content.decode('utf-8')
match = re.search(r'name=["\']csrfmiddlewaretoken["\'][^>]+value=["\']([^"\']+)["\']', html)
csrf_token = match.group(1) if match else None

if csrf_token:
    # Try POST without explicit token (testing if Client auto-includes)
    print("Testing POST without explicit CSRF token in data...")
    response = client_strict.post('/login/', {
        'email': 'Christianbituonon4@gmail.com',
        'password': 'VNxv76dBIbL@JO7UDqLo',
    })
    print(f"Status: {response.status_code}")
    if response.status_code == 302:
        print("✅ Auto-includes CSRF token")
    elif response.status_code == 403:
        print("❌ CSRF token not auto-included (403 Forbidden)")
        print("\nNow trying WITH explicit token...")
        response = client_strict.post('/login/', {
            'email': 'Christianbituonon4@gmail.com',
            'password': 'VNxv76dBIbL@JO7UDqLo',
            'csrfmiddlewaretoken': csrf_token,
        })
        print(f"Status with explicit token: {response.status_code}")
        if response.status_code == 302:
            print("✅ Works with explicit CSRF token")
else:
    print("❌ Could not extract CSRF token from form")

print("\n" + "="*80)
print("CONCLUSION:")
print("  If Method 1 works and Method 2 needs explicit token:")
print("    → TestClient requires explicit CSRF token handling")
print("    → But real browsers handle it automatically")
print("="*80)
