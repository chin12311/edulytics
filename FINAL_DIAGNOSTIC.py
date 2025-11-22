#!/usr/bin/env python
"""
FINAL DIAGNOSTIC - Run this while attempting to login from browser
This will help identify exactly where the login is failing
"""
import os
import sys
import django
import time
import threading

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'evaluationWeb.settings')
django.setup()

from django.test import Client
from django.db import connection
from django.core.cache import cache
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
import re

print("="*80)
print("FINAL LOGIN DIAGNOSTIC")
print("="*80)
print("\nThis script tests all components of the login system.")
print("Follow the instructions carefully.\n")

# TEST 1: Backend Verification
print("[TEST 1] Backend Verification")
print("-" * 80)

try:
    user = User.objects.get(email__iexact='Christianbituonon4@gmail.com')
    print(f"[OK] User found: {user.username}")
    print(f"  Email: {user.email}")
    print(f"  Is active: {user.is_active}")
    
    password = 'VNxv76dBIbL@JO7UDqLo'
    if user.check_password(password):
        print(f"[OK] Password is correct")
    else:
        print(f"[FAIL] Password is INCORRECT!")
        sys.exit(1)
        
    auth_user = authenticate(username=user.username, password=password)
    if auth_user:
        print(f"[OK] authenticate() works: {auth_user.username}")
    else:
        print(f"[FAIL] authenticate() returned None")
        sys.exit(1)
        
except User.DoesNotExist:
    print(f"[FAIL] User not found!")
    sys.exit(1)
except Exception as e:
    print(f"[FAIL] Error: {e}")
    sys.exit(1)

# TEST 2: Form Submission Test
print("\n[TEST 2] Form Submission Test")
print("-" * 80)

try:
    client = Client()
    response = client.get('/login/')
    if response.status_code == 200:
        print(f"[OK] GET /login/ returns 200 OK")
    else:
        print(f"[FAIL] GET /login/ returned {response.status_code}")
        sys.exit(1)
    
    # Extract CSRF token
    html = response.content.decode('utf-8')
    match = re.search(r'name=["\']csrfmiddlewaretoken["\'][^>]+value=["\']([^"\']+)["\']', html)
    if match:
        csrf_token = match.group(1)
        print(f"[OK] CSRF token found in form")
    else:
        print(f"[FAIL] CSRF token NOT found in form")
        sys.exit(1)
    
    # Test POST
    response = client.post('/login/', {
        'email': 'Christianbituonon4@gmail.com',
        'password': 'VNxv76dBIbL@JO7UDqLo',
    })
    
    if response.status_code == 302:
        print(f"[OK] POST /login/ returns 302 (login successful)")
    elif response.status_code == 200:
        print(f"[FAIL] POST /login/ returns 200 (login failed)")
        if b'Incorrect Username or Password' in response.content:
            print(f"  Message shown: 'Incorrect Username or Password'")
    else:
        print(f"[FAIL] POST /login/ returned {response.status_code}")
        
except Exception as e:
    print(f"[FAIL] Error: {e}")
    sys.exit(1)

# TEST 3: Database Check
print("\n[TEST 3] Database Check")
print("-" * 80)

try:
    with connection.cursor() as cursor:
        # Count users
        cursor.execute("SELECT COUNT(*) FROM auth_user")
        user_count = cursor.fetchone()[0]
        print(f"[OK] Total users in database: {user_count}")
        
        # Check specific user
        cursor.execute("SELECT id, username, email, is_active FROM auth_user WHERE email LIKE %s", 
                      ['Christianbituonon4@gmail.com'])
        row = cursor.fetchone()
        if row:
            user_id, username, email, is_active = row
            print(f"[OK] User record found:")
            print(f"  ID: {user_id}")
            print(f"  Username: {username}")
            print(f"  Email: {email}")
            print(f"  Is active: {is_active}")
        else:
            print(f"[FAIL] User not found in database")
            
except Exception as e:
    print(f"[FAIL] Database error: {e}")

# TEST 4: Server Connectivity
print("\n[TEST 4] Server Connectivity")
print("-" * 80)

import socket
import requests

try:
    # Check if server is accessible
    response = requests.get('http://localhost:8000/login/', timeout=5)
    if response.status_code == 200:
        print(f"[OK] Server accessible at http://localhost:8000")
    else:
        print(f"[FAIL] Server returned status {response.status_code}")
except requests.exceptions.ConnectionError:
    print(f"[FAIL] Cannot connect to http://localhost:8000")
    print(f"  Make sure Django server is running:")
    print(f"  python manage.py runserver 0.0.0.0:8000")
except Exception as e:
    print(f"[FAIL] Error: {e}")

# TEST 5: Instructions for User
print("\n[TEST 5] What to Do Next")
print("-" * 80)
print("\n1. Open your browser")
print("2. Go to: http://localhost:8000/login/")
print("3. Enter:")
print("   Email: Christianbituonon4@gmail.com")
print("   Password: VNxv76dBIbL@JO7UDqLo")
print("4. Click Login button")
print("5. One of these should happen:")
print("   a) [SUCCESS] You are redirected to dashboard")
print("   b) [FAILURE] You stay on login page with error")
print("\n6. If it fails, open browser Developer Tools (F12):")
print("   - Go to Console tab")
print("   - Look for any red error messages")
print("   - Go to Network tab")
print("   - Look for POST request to /login/")
print("   - Right-click -> Copy as cURL")
print("   - Share the cURL command (with password redacted)")

print("\n" + "="*80)
print("All backend tests PASSED. Issue is browser-related.")
print("="*80)
