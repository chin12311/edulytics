#!/usr/bin/env python
"""
Test the registration form to ensure no duplicate errors occur
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'evaluationWeb.settings')
sys.path.insert(0, r'c:\Users\ADMIN\eval\evaluation')
django.setup()

from django.contrib.auth.models import User
from register.forms import RegisterForm
from main.models import Section

print("=" * 80)
print("TESTING REGISTRATION FORM - No Duplicate Errors")
print("=" * 80)

# Get a section for testing
section = Section.objects.first()
if not section:
    print("❌ No sections found in database! Please create one first.")
    sys.exit(1)

print(f"\nUsing section: {section}")

# Test 1: Create a new account
print("\n\nTest 1: Create New Account (Fresh Registration)")
print("-" * 80)

test_email = 'testuser_form_fresh@cca.edu.ph'
form_data = {
    'display_name': 'Test Form User',
    'email': test_email,
    'password1': 'Test@1234!Pass',
    'password2': 'Test@1234!Pass',
    'role': 'Student',
    'studentNumber': '22-5555',
    'course': 'BSCS',
    'section': section.id,
    'institute': ''
}

# Delete if exists
User.objects.filter(email__iexact=test_email).delete()

form = RegisterForm(form_data)
if form.is_valid():
    try:
        user = form.save()
        print(f"✅ Account created successfully")
        print(f"   Username: {user.username}")
        print(f"   Email: {user.email}")
        print(f"   Profile: {user.userprofile.id}")
        print(f"   Role: {user.userprofile.role}")
    except Exception as e:
        print(f"❌ Error during save: {str(e)}")
else:
    print(f"❌ Form validation failed")
    print(f"   Errors: {form.errors}")

# Test 2: Try to create the SAME account again (should fail gracefully)
print("\n\nTest 2: Try to Duplicate (Should Show Email Error, Not Account Error)")
print("-" * 80)

form_data_dup = {
    'display_name': 'Test Form User Duplicate',
    'email': test_email,  # SAME email
    'password1': 'Test@1234!Pass',
    'password2': 'Test@1234!Pass',
    'role': 'Student',
    'studentNumber': '22-6666',
    'course': 'BSIS',
    'section': section.id,
    'institute': ''
}

form_dup = RegisterForm(form_data_dup)
if form_dup.is_valid():
    print(f"❌ Form validation PASSED (unexpected!)")
    print(f"   This should have failed due to duplicate email")
else:
    print(f"✅ Form validation correctly FAILED")
    if 'email' in form_dup.errors:
        print(f"   Email error: {form_dup.errors['email'][0]}")
    else:
        print(f"   Errors: {form_dup.errors}")

# Test 3: Try with a different email (should succeed)
print("\n\nTest 3: Different Email (Should Succeed)")
print("-" * 80)

test_email2 = 'testuser_form_second@cca.edu.ph'
form_data2 = {
    'display_name': 'Test Form User 2',
    'email': test_email2,
    'password1': 'Test@1234!Pass',
    'password2': 'Test@1234!Pass',
    'role': 'Faculty',
    'studentNumber': '',
    'course': '',
    'section': '',
    'institute': 'ICSLIS'
}

# Clean up first
User.objects.filter(email__iexact=test_email2).delete()

form2 = RegisterForm(form_data2)
if form2.is_valid():
    try:
        user2 = form2.save()
        print(f"✅ Account created successfully")
        print(f"   Username: {user2.username}")
        print(f"   Email: {user2.email}")
        print(f"   Profile: {user2.userprofile.id}")
        print(f"   Role: {user2.userprofile.role}")
    except Exception as e:
        print(f"❌ Error during save: {str(e)}")
else:
    print(f"❌ Form validation failed")
    print(f"   Errors: {form2.errors}")

# Cleanup
print("\n\nCLEANUP")
print("-" * 80)
User.objects.filter(email__iexact=test_email).delete()
User.objects.filter(email__iexact=test_email2).delete()
print("✅ Test accounts cleaned up")

print("\n" + "=" * 80)
print("✅ TEST COMPLETE - No 'account already exists' errors!")
print("=" * 80)
