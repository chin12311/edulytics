#!/usr/bin/env python
import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'evaluationWeb.settings')
sys.path.insert(0, r'c:\Users\ADMIN\eval\evaluation')
django.setup()

from django.contrib.auth.models import User
from main.models import UserProfile, Role

print("=" * 80)
print("COMPREHENSIVE ACCOUNT SEARCH DIAGNOSTIC")
print("=" * 80)

# Search for johndoe
print("\n1. SEARCHING FOR 'johndoe'")
print("-" * 80)

user_by_username = User.objects.filter(username__icontains='johndoe').first()
print(f"Found by username (icontains): {user_by_username}")

if user_by_username:
    print(f"  User ID: {user_by_username.id}")
    print(f"  Username: {user_by_username.username}")
    print(f"  Email: {user_by_username.email}")
    
    try:
        profile = user_by_username.userprofile
        print(f"  ✅ Profile exists: {profile.id}")
        print(f"     Role: {profile.role}")
        print(f"     Role == STUDENT: {profile.role == Role.STUDENT}")
        print(f"     Role == 'Student': {profile.role == 'Student'}")
        print(f"     Display Name: {profile.display_name}")
        
        # Try to query it back
        in_student_query = UserProfile.objects.filter(role=Role.STUDENT).filter(id=profile.id).exists()
        print(f"     In student query: {in_student_query}")
        
    except UserProfile.DoesNotExist:
        print(f"  ❌ Profile DOES NOT EXIST!")

# Check all recently created accounts
print("\n\n2. ALL RECENTLY CREATED ACCOUNTS (ID DESC)")
print("-" * 80)

recent = User.objects.order_by('-id')[:10]
for user in recent:
    try:
        profile = user.userprofile
        visible = UserProfile.objects.filter(role=Role.STUDENT).filter(id=profile.id).exists()
        print(f"✓ {user.username:20} | Role: {profile.role:15} | Visible: {visible}")
    except UserProfile.DoesNotExist:
        print(f"❌ {user.username:20} | NO PROFILE")

# Try searching by username
print("\n\n3. SEARCH TEST - Finding 'john' anywhere")
print("-" * 80)

search_results = User.objects.filter(
    username__icontains='john'
) | User.objects.filter(
    email__icontains='john'
)

print(f"Results: {search_results.count()}")
for user in search_results:
    try:
        profile = user.userprofile
        print(f"  - {user.username} ({user.email}) - Role: {profile.role}")
    except:
        print(f"  - {user.username} ({user.email}) - NO PROFILE")

# Check the Role enum
print("\n\n4. ROLE ENUM CHECK")
print("-" * 80)
print(f"Role.STUDENT value: {repr(Role.STUDENT)}")
print(f"Role.STUDENT == 'Student': {Role.STUDENT == 'Student'}")

# Count by role
print("\n\n5. COUNT BY ROLE")
print("-" * 80)
for role_val in [Role.STUDENT, Role.FACULTY, Role.DEAN, Role.COORDINATOR, Role.ADMIN]:
    count = UserProfile.objects.filter(role=role_val).count()
    print(f"{role_val:15} : {count}")

# Check for NULL or unusual roles
print("\n\n6. CHECKING FOR UNUSUAL ROLES")
print("-" * 80)
unusual = UserProfile.objects.exclude(
    role__in=[Role.STUDENT, Role.FACULTY, Role.DEAN, Role.COORDINATOR, Role.ADMIN]
)
print(f"Profiles with unusual roles: {unusual.count()}")
if unusual.exists():
    for profile in unusual:
        print(f"  - {profile.user.username}: role={repr(profile.role)}")

print("\n" + "=" * 80)
