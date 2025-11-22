#!/usr/bin/env python
# -*- coding: utf-8 -*-
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
import re

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
print(f"Password: {password[:10]}...")

# Step 1: GET the login form to get CSRF token
print("\n[STEP 1] GET login page")
response = client.get('/login/')
print(f"  Response Status: {response.status_code}")

# Step 2: Extract CSRF token from response
html = response.content.decode('utf-8', errors='ignore')
match = re.search(r"name='csrfmiddlewaretoken'\s+value='([^']+)'", html)
if not match:
    match = re.search(r'name="csrfmiddlewaretoken"\s+value="([^"]+)"', html)
    
if match:
    csrf_token = match.group(1)
    print(f"  CSRF Token found: YES ({len(csrf_token)} chars)")
else:
    csrf_token = ""
    print(f"  CSRF Token found: NO")

# Step 3: POST login form
print("\n[STEP 2] POST login form")
response = client.post('/login/', {
    'email': user.email,
    'password': password,
}, follow=False)

print(f"  Response Status: {response.status_code}")

if response.status_code == 302:
    location = response.get('Location', 'unknown')
    print(f"  Result: SUCCESS - Redirected to {location}")
elif response.status_code == 200:
    print(f"  Result: FAILED - Stayed on login page")
    # Check for error message
    if b'Incorrect' in response.content:
        print(f"  Error shown: 'Incorrect Username or Password'")
    if b'form-control' in response.content:
        print(f"  Form re-rendered")
else:
    print(f"  Result: UNEXPECTED - Status code {response.status_code}")

print("\n" + "="*80)
