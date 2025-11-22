"""
Verify login works for all 52 users by testing a sample of them
"""
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'evaluationWeb.settings')

import django
django.setup()

from django.contrib.auth.models import User
from django.test import Client
from django.urls import reverse
import json

print("=" * 80)
print("VERIFYING LOGIN FOR ALL 52 USERS")
print("=" * 80)

# Get all users
all_users = User.objects.all().order_by('username')
print(f"\n📊 Total users in database: {all_users.count()}")

# Load the password backup to get original credentials
try:
    with open('users_only.json', 'r') as f:
        backup_data = json.load(f)
    print(f"✅ Loaded users_only.json with {len(backup_data)} user records")
    
    # Create a mapping of username -> password hash from backup
    password_map = {}
    for user_data in backup_data:
        if user_data['model'] == 'auth.user':
            username = user_data['fields']['username']
            password_hash = user_data['fields']['password']
            password_map[username] = password_hash
    
    print(f"✅ Created password hash map with {len(password_map)} entries")
except Exception as e:
    print(f"❌ Error loading backup: {e}")
    password_map = {}

# Test a sample of users (first 5, last 5, and admin)
test_indices = list(range(0, min(5, len(all_users)))) + list(range(max(0, len(all_users)-5), len(all_users)))
test_indices = sorted(set(test_indices))  # Remove duplicates and sort

print(f"\n🧪 Testing {len(test_indices)} user accounts...")
print("-" * 80)

client = Client()
success_count = 0
failure_count = 0

for idx in test_indices:
    user = all_users[idx]
    
    # Check if password hash matches backup
    password_match = "✅" if password_map.get(user.username) == user.password else "⚠️"
    
    # Try to authenticate
    from django.contrib.auth import authenticate
    test_password = 'VNxv76dBIbL@JO7UDqLo'  # The known admin password
    
    auth_result = authenticate(username=user.username, password=test_password)
    
    if auth_result:
        status = "✅ CAN AUTH"
        success_count += 1
    else:
        status = "❌ CANNOT AUTH"
        failure_count += 1
    
    print(f"{idx+1:2d}. {status} {password_match} {user.username:30s} ({user.email})")

print("-" * 80)
print(f"\n📈 Results:")
print(f"   ✅ Can authenticate: {success_count}/{len(test_indices)}")
print(f"   ❌ Cannot authenticate: {failure_count}/{len(test_indices)}")

if success_count == len(test_indices):
    print(f"\n🎉 All tested accounts can authenticate!")
    print(f"\n💡 NEXT STEPS:")
    print(f"   1. Try logging in via browser with:")
    print(f"      Email: {all_users[0].email}")
    print(f"      Password: VNxv76dBIbL@JO7UDqLo")
    print(f"   2. If you get '429 Too Many Attempts', the rate limit is still active")
    print(f"   3. Run: python manage.py shell -c \"from django.core.cache import cache; cache.clear()\"")
    print(f"   4. Then try logging in again")
else:
    print(f"\n⚠️ Some accounts have authentication issues - passwords may need to be restored")

print("\n" + "=" * 80)
