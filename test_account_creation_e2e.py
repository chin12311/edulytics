#!/usr/bin/env python
"""
End-to-End Test: Verify account creation works completely
This tests the entire flow from User creation to profile visibility
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'evaluationWeb.settings')
sys.path.insert(0, r'c:\Users\ADMIN\eval\evaluation')
django.setup()

from django.contrib.auth.models import User
from main.models import UserProfile, Role, Section
import logging

logger = logging.getLogger(__name__)

print("=" * 80)
print("END-TO-END TEST: Account Creation Flow")
print("=" * 80)

# Test 1: Create a student account (simulating registration form)
print("\n1. TEST: Creating Student Account")
print("-" * 80)

username = 'test_student_e2e'
email = 'test_student@cca.edu.ph'

# Delete if exists
User.objects.filter(username=username).delete()

try:
    # Create user (simulates form.save())
    print(f"   Creating User: {username} ({email})")
    user = User.objects.create_user(
        username=username,
        email=email,
        password='TestPass123!'
    )
    print(f"   ✅ User created: {user.id}")
    
    # Check if profile was auto-created by signal
    try:
        profile = user.userprofile
        print(f"   ✅ Profile auto-created by signal!")
        print(f"      Profile ID: {profile.id}")
        print(f"      Temp Role: {profile.role}")
    except UserProfile.DoesNotExist:
        print(f"   ❌ Profile NOT auto-created! Signal not working!")
        sys.exit(1)
    
    # Now simulate form updating the profile (like RegisterForm.save() does)
    print(f"\n   Updating profile with student data (like form does)")
    profile.role = Role.STUDENT
    profile.studentnumber = '22-1234'
    profile.course = 'BSCS'
    profile.display_name = 'Test Student'
    
    # Validate and save
    profile.full_clean()
    profile.save(skip_validation=True)
    print(f"   ✅ Profile updated with correct role/data")
    
    # Check if account appears in student list
    students = UserProfile.objects.filter(role=Role.STUDENT)
    found = students.filter(user=user).exists()
    
    if found:
        print(f"   ✅ Account visible in student list!")
    else:
        print(f"   ❌ Account NOT visible in student list!")
        sys.exit(1)
        
except Exception as e:
    print(f"   ❌ ERROR: {str(e)}")
    sys.exit(1)

# Test 2: Create a faculty account
print("\n2. TEST: Creating Faculty Account")
print("-" * 80)

username2 = 'test_faculty_e2e'
email2 = 'test_faculty@cca.edu.ph'

User.objects.filter(username=username2).delete()

try:
    # Create user
    print(f"   Creating User: {username2} ({email2})")
    user2 = User.objects.create_user(
        username=username2,
        email=email2,
        password='TestPass123!'
    )
    print(f"   ✅ User created: {user2.id}")
    
    # Check profile
    profile2 = user2.userprofile
    print(f"   ✅ Profile auto-created: {profile2.id}")
    
    # Update as faculty
    print(f"   Updating profile as Faculty")
    profile2.role = Role.FACULTY
    profile2.institute = 'CCA'
    profile2.display_name = 'Test Faculty'
    
    profile2.full_clean()
    profile2.save(skip_validation=True)
    print(f"   ✅ Profile updated")
    
    # Check if visible in faculty list
    faculties = UserProfile.objects.filter(role=Role.FACULTY)
    found2 = faculties.filter(user=user2).exists()
    
    if found2:
        print(f"   ✅ Account visible in faculty list!")
    else:
        print(f"   ❌ Account NOT visible in faculty list!")
        sys.exit(1)
        
except Exception as e:
    print(f"   ❌ ERROR: {str(e)}")
    sys.exit(1)

# Test 3: Verify all students are queryable
print("\n3. TEST: Query all students")
print("-" * 80)

try:
    all_students = UserProfile.objects.filter(role=Role.STUDENT).select_related('user')
    count = all_students.count()
    print(f"   Total students in database: {count}")
    
    # Check if our test student is there
    test_student_found = all_students.filter(user__username=username).exists()
    if test_student_found:
        print(f"   ✅ Test student found in queryable results")
    else:
        print(f"   ❌ Test student NOT found!")
        sys.exit(1)
    
except Exception as e:
    print(f"   ❌ ERROR: {str(e)}")
    sys.exit(1)

# Cleanup
print("\n4. CLEANUP: Removing test accounts")
print("-" * 80)

try:
    User.objects.filter(username=username).delete()
    User.objects.filter(username=username2).delete()
    print(f"   ✅ Test accounts cleaned up")
except Exception as e:
    print(f"   ❌ Cleanup error: {str(e)}")

# Final verification
print("\n" + "=" * 80)
print("FINAL VERIFICATION")
print("=" * 80)

users_count = User.objects.count()
profiles_count = UserProfile.objects.count()
orphaned = User.objects.filter(userprofile__isnull=True).count()

print(f"\nTotal User records: {users_count}")
print(f"Total UserProfile records: {profiles_count}")
print(f"Orphaned records: {orphaned}")

if orphaned == 0:
    print(f"\n✅ SUCCESS! All tests passed!")
    print(f"   - Signal auto-creates profiles")
    print(f"   - Accounts appear in filtered lists")
    print(f"   - No orphaned records")
    print(f"   - End-to-end flow works correctly")
else:
    print(f"\n❌ FAILED! Found {orphaned} orphaned records")
    sys.exit(1)

print("\n" + "=" * 80)
