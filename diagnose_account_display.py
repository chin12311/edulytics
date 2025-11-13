#!/usr/bin/env python
"""
Diagnostic script to check why newly added accounts aren't displaying
"""

import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'evaluationWeb.settings')
django.setup()

from django.contrib.auth.models import User
from main.models import UserProfile, Role

print("\n" + "="*80)
print("ACCOUNT DISPLAY DIAGNOSTIC")
print("="*80)

# Check total users
print("\n1️⃣  USER COUNTS:")
print("-" * 80)
total_users = User.objects.count()
print(f"Total Django Users: {total_users}")

# Check profiles by role
print("\n2️⃣  USER PROFILES BY ROLE:")
print("-" * 80)

roles = [Role.ADMIN, Role.STUDENT, Role.DEAN, Role.COORDINATOR, Role.FACULTY]
for role in roles:
    count = UserProfile.objects.filter(role=role).count()
    print(f"{role.upper():15} {count:3} users")

# Check for students with None role
print("\n3️⃣  CHECKING FOR PROFILE ANOMALIES:")
print("-" * 80)

none_role_profiles = UserProfile.objects.filter(role__isnull=True)
if none_role_profiles.exists():
    print(f"⚠️  Found {none_role_profiles.count()} profiles with NULL role:")
    for profile in none_role_profiles[:10]:
        print(f"   - {profile.user.username} ({profile.user.email})")
else:
    print("✅ No profiles with NULL role")

# Check users without profiles
print("\n4️⃣  CHECKING ORPHANED USERS:")
print("-" * 80)

users_without_profile = User.objects.exclude(
    id__in=UserProfile.objects.values_list('user_id', flat=True)
)

if users_without_profile.exists():
    print(f"⚠️  Found {users_without_profile.count()} users without profiles:")
    for user in users_without_profile[:10]:
        print(f"   - {user.username} ({user.email}) - Created: {user.date_joined}")
else:
    print("✅ No orphaned users found")

# Check for incomplete student profiles
print("\n5️⃣  CHECKING INCOMPLETE STUDENT PROFILES:")
print("-" * 80)

students = UserProfile.objects.filter(role=Role.STUDENT)
incomplete = students.filter(course__isnull=True) | students.filter(course='')

if incomplete.exists():
    print(f"⚠️  Found {incomplete.count()} incomplete student profiles:")
    for profile in incomplete[:10]:
        print(f"   - {profile.user.username}: course='{profile.course}', section={profile.section}")
else:
    print("✅ All student profiles are complete")

# Show recent accounts
print("\n6️⃣  MOST RECENTLY CREATED ACCOUNTS:")
print("-" * 80)

recent_users = User.objects.order_by('-date_joined')[:10]
for i, user in enumerate(recent_users, 1):
    try:
        profile = user.userprofile
        print(f"{i}. {user.username:20} ({user.email:30}) - Role: {profile.role:15} Created: {user.date_joined}")
    except:
        print(f"{i}. {user.username:20} ({user.email:30}) - ⚠️  NO PROFILE - Created: {user.date_joined}")

# Check if students are actually being returned by the query used in index view
print("\n7️⃣  TESTING INDEX VIEW QUERY:")
print("-" * 80)

students_list = UserProfile.objects.filter(role=Role.STUDENT).select_related('user')
print(f"Query: UserProfile.objects.filter(role=Role.STUDENT)")
print(f"Returns: {students_list.count()} students")

if students_list.count() > 0:
    print("\nFirst 5 students found:")
    for i, student in enumerate(students_list[:5], 1):
        print(f"  {i}. {student.user.username} ({student.user.email}) - Course: {student.course}")
else:
    print("⚠️  NO STUDENTS FOUND! Check if any have role=STUDENT")

# Check pagination
print("\n8️⃣  PAGINATION CHECK:")
print("-" * 80)

from django.core.paginator import Paginator
paginator = Paginator(students_list, 25)
print(f"Total pages: {paginator.num_pages}")
print(f"Total items: {paginator.count}")
print(f"Items per page: 25")

if paginator.num_pages > 0:
    last_page = paginator.get_page(paginator.num_pages)
    print(f"\nLast page has {len(last_page.object_list)} items")

print("\n" + "="*80)
print("END DIAGNOSTIC")
print("="*80 + "\n")
