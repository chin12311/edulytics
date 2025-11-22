#!/usr/bin/env python
"""Restore original user passwords from users_only.json backup."""

import os
import django
import json

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'evaluationWeb.settings')
django.setup()

from django.contrib.auth.models import User

# Load the backup file with original password hashes
with open('users_only.json', 'r') as f:
    data = json.load(f)

print("Restoring original passwords from backup...\n")

count = 0
for item in data:
    if item['model'] == 'auth.user':
        user_id = item['pk']
        original_hash = item['fields']['password']
        
        try:
            user = User.objects.get(pk=user_id)
            user.password = original_hash
            user.save()
            count += 1
            
            if count <= 5 or count % 10 == 0:
                print(f"✅ Restored {user.username}")
        except User.DoesNotExist:
            print(f"⚠️  User ID {user_id} not found")

print(f"\n✅ Successfully restored {count} user passwords!")
print("\nNow you can log in with your original credentials:")
print("  Email: Christianbituonon4@gmail.com")
print("  Username: Christian Bitu-onon1")
print("  Password: VNxv76dBIbL@JO7UDqLo")
