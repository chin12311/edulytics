"""
Test the complete login flow to diagnose issues
"""
import os
import sys
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'evaluationWeb.settings')

import django
django.setup()

from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.test import Client
from django.urls import reverse

print("=" * 80)
print("TESTING LOGIN FLOW")
print("=" * 80)

# Test 1: Check database state
print("\n[TEST 1] Database State")
print("-" * 80)
user_count = User.objects.count()
admin_user = User.objects.filter(username='Christian Bitu-onon1').first()
print(f"Total users in database: {user_count}")
print(f"Admin user found: {admin_user}")
if admin_user:
    print(f"  - Username: {admin_user.username}")
    print(f"  - Email: {admin_user.email}")
    print(f"  - Is active: {admin_user.is_active}")
    print(f"  - Password hash: {admin_user.password[:50]}...")

# Test 2: Direct authentication
print("\n[TEST 2] Direct Authentication (Shell)")
print("-" * 80)
email = 'Christianbituonon4@gmail.com'
password = 'VNxv76dBIbL@JO7UDqLo'

try:
    user = User.objects.get(email__iexact=email)
    print(f"✅ User lookup by email: {user.username}")
    
    auth_user = authenticate(username=user.username, password=password)
    if auth_user:
        print(f"✅ Authentication successful for username={user.username}")
    else:
        print(f"❌ Authentication FAILED for username={user.username}")
except User.DoesNotExist:
    print(f"❌ User not found with email: {email}")

# Test 3: Form submission via Django test client
print("\n[TEST 3] HTTP Form Submission (via TestClient)")
print("-" * 80)
client = Client()

# First, do a GET to get CSRF token
get_response = client.get(reverse('register:login'))
print(f"GET /login: {get_response.status_code}")

# Extract CSRF token
csrf_token = None
if 'csrftoken' in client.cookies:
    csrf_token = client.cookies['csrftoken'].value
    print(f"CSRF Token obtained: {csrf_token[:20]}...")

# Now POST the login
post_data = {
    'email': email,
    'password': password,
}
if csrf_token:
    post_data['csrfmiddlewaretoken'] = csrf_token

post_response = client.post(reverse('register:login'), post_data, follow=True)
print(f"POST /login: {post_response.status_code}")
print(f"Redirected to: {post_response.redirect_chain}")

# Check if user is authenticated in the session
if post_response.wsgi_request.user.is_authenticated:
    print(f"✅ User authenticated in session: {post_response.wsgi_request.user.username}")
else:
    print(f"❌ User NOT authenticated in session")
    print(f"   Response content preview: {post_response.content[:500].decode('utf-8', errors='ignore')}")

# Test 4: Check form validation
print("\n[TEST 4] LoginForm Validation")
print("-" * 80)
from register.forms import LoginForm

form_data = {
    'email': email,
    'password': password,
}
form = LoginForm(data=form_data)

if form.is_valid():
    print(f"✅ LoginForm is VALID")
    print(f"   Cleaned email: {form.cleaned_data['email']}")
    print(f"   Cleaned password: {'*' * len(form.cleaned_data['password'])}")
else:
    print(f"❌ LoginForm is INVALID")
    print(f"   Errors: {form.errors}")

print("\n" + "=" * 80)
print("TEST COMPLETE")
print("=" * 80)
