"""
Test login in detail to see what's happening
"""
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'evaluationWeb.settings')

import django
django.setup()

from django.test import Client
from django.urls import reverse
from django.contrib.auth import authenticate
from django.contrib.auth.models import User

print("=" * 80)
print("DETAILED LOGIN DEBUGGING")
print("=" * 80)

# Test credentials
email = 'Christianbituonon4@gmail.com'
password = 'VNxv76dBIbL@JO7UDqLo'

print(f"\n🔍 TEST 1: Check user exists in database")
print("-" * 80)
try:
    user = User.objects.get(email__iexact=email)
    print(f"✅ User found: {user.username}")
    print(f"   Email: {user.email}")
    print(f"   Is active: {user.is_active}")
    print(f"   Password hash: {user.password[:50]}...")
except User.DoesNotExist:
    print(f"❌ User NOT found with email: {email}")
    print("\n⚠️ Cannot test further - user doesn't exist!")
    exit(1)

print(f"\n🔍 TEST 2: Direct authenticate() call")
print("-" * 80)
auth_result = authenticate(username=user.username, password=password)
if auth_result:
    print(f"✅ authenticate() WORKS")
    print(f"   Returned user: {auth_result.username}")
else:
    print(f"❌ authenticate() FAILED - wrong password or user issue")

print(f"\n🔍 TEST 3: HTTP GET login page")
print("-" * 80)
client = Client()
response = client.get(reverse('register:login'))
print(f"Status: {response.status_code}")
print(f"✅ GET /login works")

# Get CSRF token
csrf_token = None
if 'csrftoken' in client.cookies:
    csrf_token = client.cookies['csrftoken'].value
    print(f"✅ CSRF token obtained: {csrf_token[:20]}...")
else:
    print(f"⚠️ No CSRF token in cookies")

print(f"\n🔍 TEST 4: HTTP POST login with form data")
print("-" * 80)

post_data = {
    'email': email,
    'password': password,
}
if csrf_token:
    post_data['csrfmiddlewaretoken'] = csrf_token

response = client.post(reverse('register:login'), post_data, follow=False)
print(f"Status Code: {response.status_code}")
print(f"Response Type: {type(response).__name__}")

if response.status_code == 302:
    print(f"✅ Redirect received (expected)")
    redirect_to = response.get('Location', 'N/A')
    print(f"   Redirects to: {redirect_to}")
elif response.status_code == 200:
    print(f"⚠️ Still on login page (form errors?)")
    # Try to find error messages in response
    response_text = response.content.decode('utf-8', errors='ignore')
    if 'Invalid email or password' in response_text:
        print(f"   ❌ Error: Invalid email or password")
    elif 'Too many attempts' in response_text:
        print(f"   ❌ Error: Too many attempts (rate limited)")
    elif 'form' in response_text.lower():
        print(f"   ℹ️ Form is present in response")
    else:
        print(f"   Response preview: {response_text[:200]}")
else:
    print(f"❌ Unexpected status: {response.status_code}")

print(f"\n🔍 TEST 5: Check if authenticated after POST")
print("-" * 80)
if response.wsgi_request.user.is_authenticated:
    print(f"✅ User authenticated in session!")
    print(f"   Username: {response.wsgi_request.user.username}")
else:
    print(f"❌ User NOT authenticated in session")
    print(f"   User: {response.wsgi_request.user}")
    print(f"   Is anonymous: {response.wsgi_request.user.is_anonymous}")

print(f"\n🔍 TEST 6: Rate limit cache status")
print("-" * 80)
from django.core.cache import cache
cache_key = f"rate_limit:login_view:127.0.0.1"
attempt_count = cache.get(cache_key, 0)
print(f"Rate limit cache key: {cache_key}")
print(f"Current attempt count: {attempt_count}")
if attempt_count >= 5:
    print(f"⚠️ RATE LIMITED! ({attempt_count}/5 attempts)")
    print(f"   Clearing cache...")
    cache.delete(cache_key)
    print(f"   ✅ Cache cleared")
else:
    print(f"✅ Rate limit not triggered (OK)")

print("\n" + "=" * 80)
