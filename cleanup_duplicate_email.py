#!/usr/bin/env python
"""
Script to find and clean up duplicate email issues in the database.
Usage: python cleanup_duplicate_email.py <email_to_search>
Example: python cleanup_duplicate_email.py "student@example.com"
"""

import os
import sys
import django
from django.conf import settings

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'evaluationWeb.settings')
django.setup()

from django.db import connection
from django.contrib.auth import get_user_model

User = get_user_model()

def search_email_in_database(email):
    """Find all records with the given email"""
    print(f"\n{'='*80}")
    print(f"Searching for email: {email}")
    print(f"{'='*80}")
    
    with connection.cursor() as cursor:
        # Check in auth_user table
        cursor.execute("""
            SELECT id, username, email, is_active, date_joined, last_login
            FROM auth_user
            WHERE email = %s
            ORDER BY date_joined DESC
        """, [email])
        
        auth_user_records = cursor.fetchall()
        
        if auth_user_records:
            print(f"\nFound {len(auth_user_records)} record(s) in auth_user:")
            print("-" * 80)
            for user_id, username, user_email, is_active, date_joined, last_login in auth_user_records:
                status = "ACTIVE" if is_active else "INACTIVE"
                print(f"\nUser ID: {user_id}")
                print(f"  Username: {username}")
                print(f"  Email: {user_email}")
                print(f"  Status: {status}")
                print(f"  Created: {date_joined}")
                print(f"  Last Login: {last_login}")
                
                # Check for related userprofile
                cursor.execute("""
                    SELECT id, role, email_verified
                    FROM main_userprofile
                    WHERE user_id = %s
                """, [user_id])
                
                profile = cursor.fetchone()
                if profile:
                    profile_id, role, email_verified = profile
                    verified = "YES" if email_verified else "NO"
                    print(f"  Profile ID: {profile_id}")
                    print(f"  Role: {role}")
                    print(f"  Email Verified: {verified}")
                else:
                    print(f"  Profile: NO PROFILE FOUND (Orphaned!)")
        else:
            print(f"\nNo records found for email: {email}")
        
        # Also check if there are any inactive records with similar emails
        cursor.execute("""
            SELECT id, username, email, is_active, date_joined
            FROM auth_user
            WHERE is_active = 0
            AND (email LIKE %s OR username LIKE %s)
            ORDER BY date_joined DESC
        """, [f"%{email}%", f"%{email.split('@')[0]}%"])
        
        inactive_similar = cursor.fetchall()
        if inactive_similar:
            print(f"\n{'='*80}")
            print(f"Found {len(inactive_similar)} INACTIVE record(s) with similar email/username:")
            print("-" * 80)
            for user_id, username, user_email, is_active, date_joined in inactive_similar:
                print(f"\nUser ID: {user_id}")
                print(f"  Username: {username}")
                print(f"  Email: {user_email}")
                print(f"  Created: {date_joined}")


def delete_user_completely(user_id):
    """Delete a user and all related records"""
    print(f"\n{'='*80}")
    print(f"Deleting User ID: {user_id}")
    print(f"{'='*80}")
    
    with connection.cursor() as cursor:
        # Get user info first
        cursor.execute("""
            SELECT username, email 
            FROM auth_user 
            WHERE id = %s
        """, [user_id])
        
        result = cursor.fetchone()
        if not result:
            print("User not found!")
            return False
        
        username, email = result
        
        print(f"\nAbout to delete:")
        print(f"  Username: {username}")
        print(f"  Email: {email}")
        
        confirm = input("\nAre you sure? Type 'yes' to confirm: ")
        if confirm.lower() != 'yes':
            print("Cancelled.")
            return False
        
        # Delete related records first (due to foreign keys)
        tables_to_check = [
            'main_userprofile',
            'main_evaluation',
            'main_evaluationresponse',
            'auth_user_groups',
            'auth_user_user_permissions',
        ]
        
        for table in tables_to_check:
            cursor.execute(f"DELETE FROM {table} WHERE user_id = %s", [user_id])
            deleted = cursor.rowcount
            if deleted > 0:
                print(f"Deleted {deleted} record(s) from {table}")
        
        # Finally delete from auth_user
        cursor.execute("DELETE FROM auth_user WHERE id = %s", [user_id])
        print(f"Deleted user from auth_user")
        
        connection.commit()
        print("\nDeletion complete!")
        return True


def show_all_users():
    """Show all users in the database"""
    print(f"\n{'='*80}")
    print("ALL USERS IN DATABASE")
    print(f"{'='*80}")
    
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT id, username, email, is_active
            FROM auth_user
            ORDER BY id
        """)
        
        users = cursor.fetchall()
        print(f"\nTotal users: {len(users)}\n")
        
        for user_id, username, email, is_active in users:
            status = "ACTIVE" if is_active else "INACTIVE"
            print(f"ID: {user_id:3} | Username: {username:30} | Email: {email:35} | {status}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("\nUsage:")
        print("  python cleanup_duplicate_email.py <email>     - Search for email")
        print("  python cleanup_duplicate_email.py --all         - Show all users")
        print("  python cleanup_duplicate_email.py --delete <id> - Delete user by ID")
        print("\nExample:")
        print("  python cleanup_duplicate_email.py student@example.com")
        print("  python cleanup_duplicate_email.py --delete 99")
        sys.exit(1)
    
    if sys.argv[1] == "--all":
        show_all_users()
    elif sys.argv[1] == "--delete":
        if len(sys.argv) < 3:
            print("Please provide a user ID to delete")
            sys.exit(1)
        try:
            user_id = int(sys.argv[2])
            delete_user_completely(user_id)
        except ValueError:
            print("User ID must be a number")
            sys.exit(1)
    else:
        search_email_in_database(sys.argv[1])
