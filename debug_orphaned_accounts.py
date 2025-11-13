#!/usr/bin/env python
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'evaluationWeb.settings')
sys.path.insert(0, r'c:\Users\ADMIN\eval\evaluation')
django.setup()

from django.contrib.auth.models import User
from main.models import UserProfile, Role

print("=" * 80)
print("INVESTIGATING ORPHANED ACCOUNTS")
print("=" * 80)

# Find users without profiles
users_without_profile = User.objects.filter(userprofile__isnull=True)
print(f"\n❌ Found {users_without_profile.count()} users WITHOUT UserProfile:")
print("-" * 80)
for user in users_without_profile:
    print(f"Username: {user.username}")
    print(f"Email: {user.email}")
    print(f"Created: {user.date_joined}")
    print()

print("\n" + "=" * 80)
print("ROOT CAUSE ANALYSIS")
print("=" * 80)

# Check if the signal is properly connected
print("\nChecking if post_save signal is connected for User model...")
from django.core.signals import request_started
from django.db.models.signals import post_save

print("\nDjango post_save signal receivers for User model:")
receivers = post_save._live_receivers(User)
print(f"Number of receivers: {len(receivers)}")
for receiver in receivers:
    print(f"  - {receiver}")

print("\n" + "=" * 80)
print("TESTING PROFILE CREATION")
print("=" * 80)

print("\nAttempting to create a test user to see if profile is auto-created...")
try:
    test_user = User.objects.create_user(
        username='testuser_profile_check',
        email='testuser@cca.edu.ph',
        password='TestPass123!'
    )
    print(f"\n✅ User created: {test_user.username}")
    
    # Check if profile exists
    try:
        profile = test_user.userprofile
        print(f"✅ UserProfile auto-created: {profile.id}")
    except UserProfile.DoesNotExist:
        print(f"❌ UserProfile NOT auto-created!")
        print(f"   This explains the orphaned accounts!")
        
        # Try to create it manually
        print(f"\n   Attempting to create profile manually...")
        profile = UserProfile.objects.create(
            user=test_user,
            role=Role.STUDENT,
            studentnumber='22-9999',
            course='BSCS'
        )
        print(f"   ✅ Profile created manually: {profile.id}")
        
    # Cleanup
    test_user.delete()
    print(f"\n✅ Test user cleaned up")
    
except Exception as e:
    print(f"❌ Error: {str(e)}")

print("\n" + "=" * 80)
