#!/usr/bin/env python
import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'evaluationWeb.settings')
sys.path.insert(0, r'c:\Users\ADMIN\eval\evaluation')
django.setup()

from django.contrib.auth.models import User
from main.models import UserProfile, Role

print("Database Status:")
print(f"Total Users: {User.objects.count()}")
print(f"Total Profiles: {UserProfile.objects.count()}")
orphaned = User.objects.filter(userprofile__isnull=True).count()
print(f"Orphaned: {orphaned}")

if orphaned > 0:
    print("\n⚠️  ORPHANED USERS FOUND:")
    for u in User.objects.filter(userprofile__isnull=True):
        print(f"  - {u.username} ({u.email})")
        
# Check students
students = UserProfile.objects.filter(role=Role.STUDENT)
print(f"\nStudents visible in system: {students.count()}")
