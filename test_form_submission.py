#!/usr/bin/env python
"""
Test form submission via HTTP
"""
import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'evaluationWeb.settings')
django.setup()

from django.test import Client
from django.contrib.auth.models import User

client = Client()

# Get first user
user = User.objects.filter(email="Christianbituonon4@gmail.com").first()
if not user:
    user = User.objects.first()

password = "VNxv76dBIbL@JO7UDqLo"  # We know this works

print("="*80)
print("HTTP FORM SUBMISSION TEST")
print("="*80)

print(f"\nUser: {user.username} ({user.email})")
print(f"Password: {password}")

# Step 1: GET the login form to get CSRF token
print("\n[STEP 1] GET login page")
response = client.get('/login/')
print(f"  Status: {response.status_code}")

# Step 2: Extract CSRF token from the response
import re
match = re.search(r"name='csrfmiddlewaretoken'\s+value='([^']+)'", response.content.decode('utf-8', errors='ignore'))
if match:
    csrf_token = match.group(1)
    print(f"  CSRF Token: {csrf_token[:20]}...")
else:
    csrf_token = None
    print(f"  ❌ CSRF Token not found in response!")

# Step 3: POST login form
print("\n[STEP 2] POST login form")
response = client.post('/login/', {
    'email': user.email,
    'password': password,
    'csrfmiddlewaretoken': csrf_token,
}, follow=False)

print(f"  Status: {response.status_code}")
print(f"  Content length: {len(response.content)}")
print(f"  Content-Type: {response.get('Content-Type')}")

# Check for redirect
if response.status_code == 302:
    print(f"  ✅ REDIRECT to: {response.get('Location')}")
elif response.status_code == 200:
    print(f"  ❌ No redirect (stayed on login page)")
    # Check for errors in response
    if b'Incorrect' in response.content:
        print(f"     Error shown: 'Incorrect Username or Password'")
    if b'form-control' in response.content:
        print(f"     Form rendered again")
    
    # Print first 500 chars of response body
    print(f"\n  Response preview:")
    print(response.content.decode('utf-8', errors='ignore')[:500])

print("\n" + "="*80)
