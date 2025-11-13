#!/usr/bin/env python
import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'evaluationWeb.settings')
sys.path.insert(0, r'c:\Users\ADMIN\eval\evaluation')
django.setup()

from django.contrib.auth.models import User
from main.models import UserProfile, Role
from datetime import datetime, timedelta

print("=" * 80)
print("CHECKING RECENTLY CREATED ACCOUNTS")
print("=" * 80)

# Get users created in last 1 hour
one_hour_ago = datetime.now() - timedelta(hours=1)
recent_users = User.objects.filter(date_joined__gte=one_hour_ago).order_by('-date_joined')

print(f"\nUsers created in last hour: {recent_users.count()}")
print("-" * 80)

for user in recent_users:
    try:
        profile = user.userprofile
        print(f"\n✓ {user.username}")
        print(f"  Email: {user.email}")
        print(f"  Profile ID: {profile.id}")
        print(f"  Role: {profile.role}")
        print(f"  Display Name: {profile.display_name}")
        if profile.role == Role.STUDENT:
            print(f"  Student #: {profile.studentnumber}")
            print(f"  Course: {profile.course}")
            # Check if visible in student list
            in_list = UserProfile.objects.filter(role=Role.STUDENT).filter(id=profile.id).exists()
            print(f"  Visible in student list: {'✅ YES' if in_list else '❌ NO'}")
    except UserProfile.DoesNotExist:
        print(f"\n❌ {user.username} - NO PROFILE!")

print("\n" + "=" * 80)
