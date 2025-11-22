"""
Test authenticate() with and without request parameter
"""
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'evaluationWeb.settings')

import django
django.setup()

from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.test import RequestFactory

print("=" * 80)
print("TESTING authenticate() WITH AND WITHOUT REQUEST")
print("=" * 80)

user = User.objects.get(email__iexact='Christianbituonon4@gmail.com')
password = 'VNxv76dBIbL@JO7UDqLo'

print(f"\n1️⃣ Test WITHOUT request parameter:")
print("-" * 80)
result1 = authenticate(username=user.username, password=password)
print(f"Result: {result1}")
if result1:
    print(f"✅ authenticate(username=..., password=...) works")
else:
    print(f"❌ authenticate(username=..., password=...) failed")

print(f"\n2️⃣ Test WITH request parameter (GET):")
print("-" * 80)
factory = RequestFactory()
request = factory.get('/')
result2 = authenticate(request=request, username=user.username, password=password)
print(f"Result: {result2}")
if result2:
    print(f"✅ authenticate(request=request, username=..., password=...) works")
else:
    print(f"❌ authenticate(request=request, username=..., password=...) failed")

print(f"\n3️⃣ Test WITH request parameter (POST):")
print("-" * 80)
request_post = factory.post('/')
result3 = authenticate(request=request_post, username=user.username, password=password)
print(f"Result: {result3}")
if result3:
    print(f"✅ authenticate(request=request_post, username=..., password=...) works")
else:
    print(f"❌ authenticate(request=request_post, username=..., password=...) failed")

print(f"\n4️⃣ Direct check_password():")
print("-" * 80)
result4 = user.check_password(password)
print(f"Result: {result4}")
if result4:
    print(f"✅ user.check_password() works")
else:
    print(f"❌ user.check_password() failed")

print(f"\n5️⃣ Test with username that has SPACES:")
print("-" * 80)
# The username is "Christian Bitu-onon1" which has spaces and special chars
print(f"Username: '{user.username}'")
print(f"Username repr: {repr(user.username)}")
print(f"Username length: {len(user.username)}")

# Try different variations
test_usernames = [
    user.username,
    user.username.strip(),
    user.username.replace(' ', ''),
    user.username.lower(),
]

for test_user in test_usernames:
    result = authenticate(username=test_user, password=password)
    status = "✅" if result else "❌"
    print(f"   {status} authenticate(username='{test_user}', ...)")

print("\n" + "=" * 80)
