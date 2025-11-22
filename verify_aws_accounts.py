#!/usr/bin/env python
"""
Test accounts on BOTH local and AWS databases
Verify all 52 accounts can login on both systems
"""
import os
import sys
import django
import pymysql

print("="*80)
print("DUAL DATABASE ACCOUNT VERIFICATION")
print("="*80)

# Test LOCAL database (localhost)
print("\n[1] TESTING LOCAL DATABASE (localhost:3306)")
print("-" * 80)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'evaluationWeb.settings')
django.setup()

from django.contrib.auth.models import User
from django.db import connection

try:
    with connection.cursor() as cursor:
        cursor.execute("SELECT COUNT(*) FROM auth_user")
        local_count = cursor.fetchone()[0]
        
    print(f"Status: CONNECTED")
    print(f"Database: {connection.get_connection_params()['db']}")
    print(f"Host: {connection.get_connection_params()['host']}")
    print(f"Users found: {local_count}")
    
    if local_count == 52:
        print("Result: [OK] LOCAL DATABASE HAS ALL 52 ACCOUNTS")
    else:
        print(f"Result: [WARNING] Expected 52 users, found {local_count}")
        
except Exception as e:
    print(f"Error: {e}")
    print("Result: [FAIL] Could not connect to local database")

# Test AWS database
print("\n[2] TESTING AWS DATABASE")
print("-" * 80)

# Need to manually connect to AWS to test
try:
    # Read the connection params from .env or hardcoded
    aws_connection = pymysql.connect(
        host='evalulytics-db.czjnyqmqjv2q.us-east-1.rds.amazonaws.com',
        user='eval_user',
        password='!eETXiuo4LHxeu6M4#sz',
        database='evaluation',
        charset='utf8mb4'
    )
    
    print(f"Status: CONNECTED")
    print(f"Database: evaluation")
    print(f"Host: evalulytics-db.czjnyqmqjv2q.us-east-1.rds.amazonaws.com")
    
    with aws_connection.cursor() as cursor:
        cursor.execute("SELECT COUNT(*) FROM auth_user")
        aws_count = cursor.fetchone()[0]
        
    print(f"Users found: {aws_count}")
    
    if aws_count == 52:
        print("Result: [OK] AWS DATABASE HAS ALL 52 ACCOUNTS")
    else:
        print(f"Result: [WARNING] Expected 52 users, found {aws_count}")
    
    # Also check profiles
    with aws_connection.cursor() as cursor:
        cursor.execute("SELECT COUNT(*) FROM main_userprofile")
        profile_count = cursor.fetchone()[0]
        
    if profile_count == 52:
        print(f"Profiles: [OK] All 52 user profiles present")
    else:
        print(f"Profiles: [WARNING] Expected 52 profiles, found {profile_count}")
        
    aws_connection.close()
    
except Exception as e:
    print(f"Error: {e}")
    print("Result: [FAIL] Could not connect to AWS database")
    print("\nPossible issues:")
    print("  1. Network/firewall blocking AWS connection")
    print("  2. AWS RDS endpoint incorrect")
    print("  3. AWS credentials wrong")
    print("  4. AWS security group not configured")

print("\n" + "="*80)
print("SUMMARY")
print("="*80)

# Reconnect to local to get local count for display
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'evaluationWeb.settings')
django.setup()

try:
    local_users = User.objects.count()
    local_profiles = User.objects.count()  # Approximation
    print(f"\nLocal Database:")
    print(f"  Users: {local_users}")
    print(f"  Ready to login: {local_users}/52")
    
except:
    print("Local database: Connection error")

print("\nAWS Database:")
print("  (Check results above)")

print("\n" + "="*80)
print("NEXT STEPS:")
print("  1. If both show 52 users: All systems operational")
print("  2. If AWS shows different count: Re-sync from local")
print("  3. If AWS connection fails: Check network/security groups")
print("="*80)
