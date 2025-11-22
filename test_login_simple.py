#!/usr/bin/env python
"""
Simple login test - verify credentials work
"""
import os
import sys
import django
import time

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'evaluationWeb.settings')
django.setup()

from django.contrib.auth.models import User
from django.test import Client

print("="*80)
print("LOGIN TEST - VERIFY CREDENTIALS WORK")
print("="*80)

# Create test client
client = Client()

# Get first user from database
users = User.objects.all()[:5]

print(f"\nTesting login for {len(users)} users...\n")

for user in users:
    print(f"User: {user.username} ({user.email})")
    print(f"  - Active: {user.is_active}")
    print(f"  - Password hash: {user.password[:40]}...")
    
    # Try to authenticate with each user
    # We know the admin password from earlier work
    if user.email == "Christianbituonon4@gmail.com":
        password = "VNxv76dBIbL@JO7UDqLo"  # Admin password
    elif user.email == "Admin@gmail.com":
        password = "Admin@123"
    else:
        password = "EduLytics@2025"  # Default test password
    
    print(f"  - Testing with password: {password[:10]}...")
    
    # Test POST to login endpoint
    try:
        response = client.post('/login/', {
            'email': user.email,
            'password': password,
        }, follow=False)
        
        print(f"  - Response status: {response.status_code}")
        
        if response.status_code == 302:
            print(f"    ✅ LOGIN SUCCESSFUL (redirected)")
        elif response.status_code == 200:
            print(f"    ❌ Form error: {response.status_code}")
            if b'Incorrect' in response.content:
                print(f"       Error shown: 'Incorrect Username or Password'")
            if b'error' in response.content:
                print(f"       Some error in response")
        else:
            print(f"    ❌ Unexpected response: {response.status_code}")
            
    except Exception as e:
        print(f"  - ❌ Error: {str(e)}")
    
    print()

print("="*80)
print("\nNOTE: Check Django server logs for authentication details")
print("="*80)
