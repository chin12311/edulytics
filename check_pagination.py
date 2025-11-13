#!/usr/bin/env python
import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'evaluationWeb.settings')
sys.path.insert(0, r'c:\Users\ADMIN\eval\evaluation')
django.setup()

from main.models import UserProfile, Role
from django.core.paginator import Paginator

print("=" * 80)
print("SIMULATING INDEX VIEW - PAGINATION CHECK")
print("=" * 80)

# Simulate what the view does
students_list = UserProfile.objects.filter(role=Role.STUDENT).select_related('user').order_by('-id')

print(f"\nTotal students in query: {students_list.count()}")
print("-" * 80)

# Apply pagination like the view does
paginator = Paginator(students_list, 25)
print(f"Total pages: {paginator.num_pages}")
print(f"Items per page: {paginator.per_page}")

# Show each page
for page_num in range(1, paginator.num_pages + 1):
    page = paginator.get_page(page_num)
    print(f"\nPage {page_num}: {page.object_list.count()} items")
    for student in page:
        print(f"  - {student.user.username} ({student.studentnumber}) - {student.course}")

print("\n" + "=" * 80)
print("LOOKING FOR RECENT ACCOUNTS")
print("=" * 80)

recent = students_list[:5]  # First 5 (most recent due to -id order)
print(f"\nMost recent 5 students:")
for student in recent:
    print(f"  - {student.user.username} ({student.user.email}) - {student.studentnumber}")

# Check if 'johndoe' is in the list
johndoe = UserProfile.objects.filter(user__username='johndoe').first()
if johndoe:
    print(f"\njohndoe status:")
    print(f"  Role: {johndoe.role}")
    print(f"  In query: {students_list.filter(id=johndoe.id).exists()}")
else:
    print("\njohndoe not found")

print("\n" + "=" * 80)
