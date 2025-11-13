#!/usr/bin/env python
"""
Create missing UserProfile records for imported users.
This fixes the "No users found" issue in the admin panel.
"""

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'evaluationWeb.settings')
django.setup()

from django.contrib.auth.models import User
from main.models import UserProfile, Role

def create_missing_profiles():
    """Create UserProfile for any User that doesn't have one."""
    
    # Get all users
    all_users = User.objects.all()
    print(f"Total users in database: {all_users.count()}")
    
    # Count existing profiles
    existing_profiles = UserProfile.objects.count()
    print(f"Existing profiles: {existing_profiles}")
    
    created_count = 0
    
    for user in all_users:
        # Check if profile exists
        if not hasattr(user, 'userprofile'):
            # Determine role based on username
            # If username is "Admin", make them admin
            # Otherwise, default to Student
            if user.username.lower() == 'admin':
                role = Role.ADMIN
            else:
                role = Role.STUDENT
            
            # Create profile
            profile = UserProfile(
                user=user,
                display_name=user.first_name or user.username,
                role=role,
                studentnumber=None if role != Role.STUDENT else '',
                course=None if role != Role.STUDENT else '',
            )
            
            # Skip validation for now
            profile.save(skip_validation=True)
            created_count += 1
            print(f"  ✅ Created profile for {user.username} (role: {role})")
    
    print(f"\n✅ Created {created_count} new UserProfile records!")
    print(f"Total profiles now: {UserProfile.objects.count()}")

if __name__ == '__main__':
    create_missing_profiles()
