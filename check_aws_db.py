#!/usr/bin/env python
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'evaluationWeb.settings')
sys.path.insert(0, '/home/ubuntu/edulytics')
django.setup()

from django.contrib.auth.models import User
from evaluation.models import UserProfile

print("=== DATABASE CHECK ===")
print(f"Total Django users: {User.objects.count()}")
print(f"Total UserProfiles: {UserProfile.objects.count()}")

# Check for specific user
user = User.objects.filter(email='Christianbituonon4@gmail.com').first()
if user:
    print(f"\nAdmin user found:")
    print(f"  Username: {user.username}")
    print(f"  Email: {user.email}")
    print(f"  Is active: {user.is_active}")
    print(f"  Is staff: {user.is_staff}")
else:
    print("\nAdmin user NOT found")

# List first 5 users
print(f"\nFirst 5 users:")
for u in User.objects.all()[:5]:
    print(f"  - {u.email} ({u.username})")
