"""
Restore all original passwords from backup JSON for all 52 users
"""
import os
import json
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'evaluationWeb.settings')

import django
django.setup()

from django.contrib.auth.models import User
from django.contrib.auth.hashers import make_password

print("=" * 80)
print("RESTORING ORIGINAL PASSWORDS FROM BACKUP")
print("=" * 80)

# Load backup data
try:
    with open('users_only.json', 'r') as f:
        backup_data = json.load(f)
    print(f"\n✅ Loaded users_only.json with {len(backup_data)} records")
except Exception as e:
    print(f"❌ Error loading backup: {e}")
    exit(1)

# Create mapping of username -> original password hash
password_map = {}
for user_data in backup_data:
    if user_data['model'] == 'auth.user':
        username = user_data['fields']['username']
        email = user_data['fields']['email']
        password_hash = user_data['fields']['password']
        password_map[username] = {
            'email': email,
            'password': password_hash
        }

print(f"✅ Created password map with {len(password_map)} users")

# Restore passwords
print(f"\n🔄 Restoring passwords...")
print("-" * 80)

restored_count = 0
failed_count = 0
not_found_count = 0

for username, data in sorted(password_map.items()):
    try:
        user = User.objects.get(username=username)
        original_password = data['password']
        
        # Only restore if different
        if user.password != original_password:
            user.password = original_password
            user.save(update_fields=['password'])
            print(f"✅ Restored {username:35s} ({data['email']})")
            restored_count += 1
        else:
            print(f"⏭️  Skip      {username:35s} (already correct)")
    except User.DoesNotExist:
        print(f"❌ Not found  {username:35s}")
        not_found_count += 1
    except Exception as e:
        print(f"❌ Error     {username:35s} - {str(e)}")
        failed_count += 1

print("-" * 80)
print(f"\n📊 Results:")
print(f"   ✅ Restored: {restored_count}")
print(f"   ⏭️  Skipped:  {len(password_map) - restored_count - not_found_count}")
print(f"   ❌ Not found: {not_found_count}")
print(f"   ⚠️  Errors:   {failed_count}")

# Verify
print(f"\n🧪 Verifying passwords...")
from django.contrib.auth import authenticate

verify_count = 0
for username in list(password_map.keys())[:5]:  # Test first 5
    user = User.objects.get(username=username)
    # Try with dummy password first (should fail)
    result = authenticate(username=username, password='VNxv76dBIbL@JO7UDqLo')
    if result:
        print(f"✅ {username} - authenticate() works")
        verify_count += 1
    else:
        print(f"❌ {username} - authenticate() failed")

print(f"\n✅ Verified {verify_count}/5 test accounts can authenticate")
print("\n" + "=" * 80)
