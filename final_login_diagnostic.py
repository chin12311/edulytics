"""
Final diagnostic - Check everything that could cause login to fail
"""
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'evaluationWeb.settings')

import django
django.setup()

from django.contrib.auth.models import User
from django.test import Client
from django.urls import reverse
import logging

# Set up logging to see all messages
logging.basicConfig(level=logging.DEBUG)

print("=" * 80)
print("COMPREHENSIVE LOGIN DIAGNOSTIC")
print("=" * 80)

print("\n✅ STEP 1: User exists in database")
print("-" * 80)
user = User.objects.get(email__iexact='Christianbituonon4@gmail.com')
print(f"✅ User: {user.username}")
print(f"   Email: {user.email}")
print(f"   Active: {user.is_active}")
print(f"   Password hash: {user.password}")

print("\n✅ STEP 2: Direct authenticate works")
print("-" * 80)
auth_result = user.check_password('VNxv76dBIbL@JO7UDqLo')
print(f"✅ check_password() result: {auth_result}")

print("\n✅ STEP 3: Simulate HTTP login")
print("-" * 80)
client = Client()

# GET login page
get_response = client.get(reverse('register:login'))
print(f"✅ GET /login/ status: {get_response.status_code}")

# POST login
post_data = {
    'email': 'Christianbituonon4@gmail.com',
    'password': 'VNxv76dBIbL@JO7UDqLo',
}
response = client.post(reverse('register:login'), post_data, follow=False)
print(f"✅ POST status: {response.status_code}")

if response.status_code == 302:
    print(f"✅ Redirected to: {response.get('Location')}")
    print(f"✅ ✅✅ LOGIN WORKS! ✅✅✅")
elif response.status_code == 200:
    print(f"⚠️ Still on login page (200 OK)")
    # Check for errors in response
    content = response.content.decode('utf-8')
    if 'non_field_errors' in content or 'Invalid email' in content:
        print(f"❌ Form has errors - authentication failed")
    else:
        print(f"ℹ️ Form returned but no obvious errors")

print("\n" + "=" * 80)
print("INSTRUCTIONS: Now try logging in from your browser")
print("=" * 80)
print(f"""
Email:    Christianbituonon4@gmail.com
Password: VNxv76dBIbL@JO7UDqLo
URL:      /login/

After clicking Login:
1. Check browser developer console (F12)
2. Look for any JavaScript errors
3. Try clearing cache (Ctrl+Shift+Delete)
4. Try different browser or incognito window
5. If still failing, tell me what you see on screen
""")
