#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'evaluationWeb.settings')
django.setup()

from django.contrib.auth.models import User
from main.models import UserProfile, Role

print('=' * 80)
print('LOCAL MYSQL DATABASE - ALL ACCOUNTS')
print('=' * 80)

total_users = User.objects.count()
print(f'\nTotal Users: {total_users}\n')

# Group by role
roles = [Role.FACULTY, Role.COORDINATOR, Role.DEAN, Role.STUDENT, Role.ADMIN]
for role in roles:
    count = UserProfile.objects.filter(role=role).count()
    print(f'  {role.value}: {count} accounts')

print('\n' + '=' * 80)
print('FACULTY ACCOUNTS')
print('=' * 80)
faculty = UserProfile.objects.filter(role=Role.FACULTY).select_related('user')
for i, profile in enumerate(faculty, 1):
    print(f'{i}. {profile.display_name} ({profile.user.username}) - {profile.user.email}')

print('\n' + '=' * 80)
print('STUDENTS (showing all)')
print('=' * 80)
students = UserProfile.objects.filter(role=Role.STUDENT).select_related('user')
for i, profile in enumerate(students, 1):
    print(f'{i}. {profile.display_name} ({profile.user.username})')

print('\n' + '=' * 80)
print('COORDINATORS')
print('=' * 80)
coordinators = UserProfile.objects.filter(role=Role.COORDINATOR).select_related('user')
for i, profile in enumerate(coordinators, 1):
    print(f'{i}. {profile.display_name} ({profile.user.username}) - {profile.user.email}')

print('\n' + '=' * 80)
print('DEANS')
print('=' * 80)
deans = UserProfile.objects.filter(role=Role.DEAN).select_related('user')
for i, profile in enumerate(deans, 1):
    print(f'{i}. {profile.display_name} ({profile.user.username}) - {profile.user.email}')

print('\n' + '=' * 80)
print('ADMIN ACCOUNTS')
print('=' * 80)
admins = UserProfile.objects.filter(role=Role.ADMIN).select_related('user')
for i, profile in enumerate(admins, 1):
    print(f'{i}. {profile.display_name} ({profile.user.username}) - {profile.user.email}')

print('\n' + '=' * 80)
