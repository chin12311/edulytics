"""
Test authentication with various passwords to find what works
"""
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'evaluationWeb.settings')

import django
django.setup()

from django.contrib.auth.models import User
from django.contrib.auth import authenticate
import json

print("=" * 80)
print("TESTING AUTHENTICATION WITH DIFFERENT PASSWORD COMBINATIONS")
print("=" * 80)

# Get a few test users
test_users = User.objects.all()[:5]

# Load backup to see what they had before
with open('users_only.json', 'r') as f:
    backup_data = json.load(f)

# Create a mapping
password_map = {}
for user_data in backup_data:
    if user_data['model'] == 'auth.user':
        username = user_data['fields']['username']
        password_map[username] = user_data['fields']['password']

print(f"\n🔐 Testing passwords for {len(test_users)} sample users...")
print("-" * 80)

# Common passwords to try
test_passwords = [
    'VNxv76dBIbL@JO7UDqLo',  # The password we used before
    'Admin@123',
    'Password@123',
    'Welcome@123',
    '123456',
    'admin',
]

for user in test_users:
    print(f"\n👤 {user.username} ({user.email})")
    print(f"   Current hash: {user.password[:40]}...")
    print(f"   Hash in backup: {password_map.get(user.username, 'N/A')[:40]}...")
    
    # Try each password
    success_found = False
    for pwd in test_passwords:
        auth_user = authenticate(username=user.username, password=pwd)
        if auth_user:
            print(f"   ✅ WORKS with: '{pwd}'")
            success_found = True
            break
    
    if not success_found:
        print(f"   ❌ NONE of the test passwords worked")

print("\n" + "=" * 80)
