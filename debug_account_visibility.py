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
print("DATABASE INSPECTION - Account Creation Issue Debug")
print("=" * 80)

# 1. Check ALL UserProfiles
print("\n1. ALL USERPROFILES IN DATABASE:")
print("-" * 80)
all_profiles = UserProfile.objects.all().select_related('user')
print(f"Total profiles: {all_profiles.count()}")
for profile in all_profiles:
    print(f"\n  Username: {profile.user.username}")
    print(f"  Email: {profile.user.email}")
    print(f"  Role: {profile.role!r}")
    print(f"  Role Type: {type(profile.role)}")
    print(f"  Display Name: {profile.display_name}")
    if profile.role == 'Student':
        print(f"  Student Number: {profile.studentnumber}")
        print(f"  Course: {profile.course}")

# 2. Check STUDENT profiles specifically
print("\n\n2. STUDENT PROFILES (filtering by role='Student'):")
print("-" * 80)
students = UserProfile.objects.filter(role='Student').select_related('user')
print(f"Students with role='Student': {students.count()}")
for student in students:
    print(f"  - {student.user.username} ({student.user.email})")

# 3. Check STUDENT profiles using Role.STUDENT
print("\n3. STUDENT PROFILES (filtering by Role.STUDENT):")
print("-" * 80)
print(f"Role.STUDENT value: {Role.STUDENT!r}")
students_enum = UserProfile.objects.filter(role=Role.STUDENT).select_related('user')
print(f"Students with role=Role.STUDENT: {students_enum.count()}")
for student in students_enum:
    print(f"  - {student.user.username} ({student.user.email})")

# 4. Check for any role mismatches
print("\n4. CHECKING FOR ROLE MISMATCHES:")
print("-" * 80)
valid_roles = [Role.STUDENT, Role.DEAN, Role.FACULTY, Role.COORDINATOR, Role.ADMIN]
print(f"Valid roles: {valid_roles}")
all_roles_in_db = UserProfile.objects.values_list('role', flat=True).distinct()
print(f"Actual roles in DB: {list(all_roles_in_db)}")

invalid_profiles = UserProfile.objects.exclude(role__in=valid_roles)
if invalid_profiles.exists():
    print(f"\n❌ FOUND INVALID PROFILES: {invalid_profiles.count()}")
    for profile in invalid_profiles:
        print(f"  - {profile.user.username}: role={profile.role!r}")
else:
    print("\n✅ All profiles have valid roles")

# 5. Check for validation errors
print("\n5. CHECKING PROFILE VALIDATION:")
print("-" * 80)
for profile in all_profiles:
    try:
        profile.clean()
        print(f"✅ {profile.user.username}: Valid")
    except Exception as e:
        print(f"❌ {profile.user.username}: {str(e)}")

# 6. Raw database query
print("\n6. RAW DATABASE QUERY:")
print("-" * 80)
from django.db import connection
cursor = connection.cursor()
cursor.execute("""
    SELECT 
        u.username, 
        u.email, 
        p.role, 
        p.studentnumber,
        p.course
    FROM auth_user u
    LEFT JOIN main_userprofile p ON u.id = p.user_id
    ORDER BY p.role, u.username
""")
rows = cursor.fetchall()
print(f"{'Username':<20} {'Email':<30} {'Role':<15} {'Student #':<10} {'Course':<20}")
print("-" * 95)
for row in rows:
    username, email, role, stnum, course = row
    print(f"{username:<20} {email:<30} {str(role):<15} {str(stnum):<10} {str(course):<20}")

print("\n" + "=" * 80)
print("END DEBUG")
print("=" * 80)
