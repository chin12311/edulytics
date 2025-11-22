#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'evaluationWeb.settings')
django.setup()

from django.contrib.auth.models import User
from main.models import UserProfile

total = User.objects.count()
profiles = UserProfile.objects.count()

print(f"Total User accounts: {total}")
print(f"Total UserProfile records: {profiles}")
print()

if total > 0:
    print("First 10 user accounts:")
    for i, user in enumerate(User.objects.all()[:10], 1):
        print(f"  {i}. {user.username} - {user.email}")
else:
    print("NO USERS FOUND!")
