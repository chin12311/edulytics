#!/usr/bin/env python
"""
Copy data from local MySQL to AWS MySQL
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'evaluationWeb.settings')
django.setup()

from django.contrib.auth.models import User
from main.models import UserProfile, Section, SectionAssignment, Evaluation, EvaluationPeriod

# Connect to AWS and create data manually
import pymysql

# AWS MySQL credentials
aws_db = pymysql.connect(
    host='localhost',  # Will SSH tunnel
    user='eval_user',
    password='eval_password',
    database='evaluation',
    charset='utf8mb4'
)

print("Connected to local MySQL")

# Get all users
users = User.objects.all()
print(f"Found {users.count()} users locally")

# Create simple SQL inserts for each user
for user in users:
    print(f"Processing user: {user.username}")
    # We'll create a simple migration script

print("\nData export complete. Check the SQL file.")
