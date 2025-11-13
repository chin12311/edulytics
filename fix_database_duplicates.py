#!/usr/bin/env python
"""
Script to completely remove a user account from the database.
This removes from ALL related tables, not just auth_user.

Usage:
    python fix_database_duplicates.py <user_id>     - Delete by user ID
    python fix_database_duplicates.py --email <email> - Delete by email
    python fix_database_duplicates.py --search <email> - Search for email
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


def search_email(email):
    """Search for a user by email"""
    print(f"\n{'='*80}")
    print(f"Searching for email: {email}")
    print(f"{'='*80}\n")
    
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT id, username, email, is_active, date_joined
            FROM auth_user
            WHERE email = %s
            ORDER BY date_joined DESC
        """, [email])
        
        records = cursor.fetchall()
        
        if records:
            for user_id, username, user_email, is_active, date_joined in records:
                status = "ACTIVE" if is_active else "INACTIVE"
                print(f"User ID: {user_id}")
                print(f"  Username: {username}")
                print(f"  Email: {user_email}")
                print(f"  Status: {status}")
                print(f"  Created: {date_joined}")
                print()
        else:
            print(f"No user found with email: {email}")


def count_related_records(user_id):
    """Count how many related records will be deleted"""
    print(f"\n{'='*80}")
    print(f"Records to be deleted for User ID: {user_id}")
    print(f"{'='*80}\n")
    
    tables_and_columns = {
        'main_userprofile': 'user_id',
        'main_evaluation': 'user_id',
        'main_evaluationresponse': 'user_id',
        'main_evaluationresult': 'user_id',
        'main_evaluationhistory': 'user_id',
        'main_recommendation': 'user_id',
        'main_adminactivitylog': 'target_user_id',
        'main_sectionassignment': 'user_id',
        'auth_user_groups': 'user_id',
        'auth_user_user_permissions': 'user_id',
    }
    
    total_records = 0
    
    with connection.cursor() as cursor:
        for table, column in tables_and_columns.items():
            cursor.execute(f"""
                SELECT COUNT(*) 
                FROM {table} 
                WHERE {column} = %s
            """, [user_id])
            
            count = cursor.fetchone()[0]
            if count > 0:
                print(f"  {table}: {count} record(s)")
                total_records += count
    
    print(f"\nTotal related records: {total_records}")
    return total_records


def delete_user_completely(user_id):
    """Delete a user and ALL related records from database"""
    print(f"\n{'='*80}")
    print(f"COMPLETE USER DELETION - User ID: {user_id}")
    print(f"{'='*80}\n")
    
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
        
        print(f"User Details:")
        print(f"  ID: {user_id}")
        print(f"  Username: {username}")
        print(f"  Email: {email}")
        
        # Count related records
        count_related_records(user_id)
        
        # Ask for confirmation
        confirm = input("\nAre you sure you want to DELETE this account permanently? ")
        confirm = confirm.strip().lower()
        if confirm not in ['yes', 'y']:
            print("Cancelled.")
            return False
        
        # Double confirmation for safety
        confirm2 = input("Type 'DELETE' to confirm permanent deletion: ")
        if confirm2 != "DELETE":
            print("Cancelled.")
            return False
        
        print("\nDeleting records...")
        
        # Delete in order of dependencies
        delete_commands = [
            ('main_adminactivitylog', 'target_user_id'),
            ('main_evaluationresponse', 'user_id'),
            ('main_evaluationresult', 'user_id'),
            ('main_evaluationhistory', 'user_id'),
            ('main_evaluation', 'user_id'),
            ('main_recommendation', 'user_id'),
            ('main_sectionassignment', 'user_id'),
            ('main_userprofile', 'user_id'),
            ('auth_user_groups', 'user_id'),
            ('auth_user_user_permissions', 'user_id'),
            ('auth_user', 'id'),
        ]
        
        for table, column in delete_commands:
            cursor.execute(f"DELETE FROM {table} WHERE {column} = %s", [user_id])
            deleted = cursor.rowcount
            if deleted > 0:
                print(f"  ✓ Deleted {deleted} record(s) from {table}")
        
        connection.commit()
        
        print(f"\n{'='*80}")
        print("SUCCESS: User account completely deleted from database!")
        print(f"  Username: {username}")
        print(f"  Email: {email} (now available for new signup)")
        print(f"{'='*80}\n")
        
        return True


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("\nUsage:")
        print("  python fix_database_duplicates.py --search <email>")
        print("  python fix_database_duplicates.py <user_id>")
        print("\nExamples:")
        print("  python fix_database_duplicates.py --search student@example.com")
        print("  python fix_database_duplicates.py 99")
        print("\n")
        sys.exit(1)
    
    try:
        if sys.argv[1] == "--search":
            if len(sys.argv) < 3:
                print("Please provide an email address to search")
                sys.exit(1)
            search_email(sys.argv[2])
        else:
            user_id = int(sys.argv[1])
            delete_user_completely(user_id)
    except ValueError:
        print("User ID must be a number")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {str(e)}")
        sys.exit(1)
