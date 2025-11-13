#!/usr/bin/env python
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'evaluationWeb.settings')
sys.path.insert(0, r'c:\Users\ADMIN\eval\evaluation')
django.setup()

from django.contrib.auth.models import User
from register.forms import RegisterForm

print("=" * 80)
print("TESTING REGISTRATION FORM - 'ACCOUNT ALREADY EXISTS' ISSUE")
print("=" * 80)

# Test 1: Try registering with a brand new email
print("\nTest 1: Brand New Email (Should Succeed)")
print("-" * 80)

test_email = 'brand_new_test_99@cca.edu.ph'
form_data = {
    'display_name': 'Test Student New',
    'email': test_email,
    'password1': 'Test@1234!Pass',
    'password2': 'Test@1234!Pass',
    'role': 'Student',
    'studentNumber': '99-9999',
    'course': 'BSCS',
    'section': 1,  # Assuming section ID 1 exists
    'institute': ''
}

form = RegisterForm(form_data)
if form.is_valid():
    print(f"✅ Form validation PASSED")
    print(f"   Email: {test_email}")
    print(f"   Username would be: {form.final_username if hasattr(form, 'final_username') else 'N/A'}")
else:
    print(f"❌ Form validation FAILED")
    print(f"   Errors: {form.errors}")

# Test 2: Try with an email that already exists
print("\n\nTest 2: Duplicate Email (Should Fail with proper error)")
print("-" * 80)

# Find an existing email
existing_user = User.objects.first()
if existing_user:
    dup_email = existing_user.email
    print(f"Found existing email: {dup_email}")
    
    form_data2 = {
        'display_name': 'Duplicate Test',
        'email': dup_email,
        'password1': 'Test@1234!Pass',
        'password2': 'Test@1234!Pass',
        'role': 'Student',
        'studentNumber': '88-8888',
        'course': 'BSIS',
        'section': 1,
        'institute': ''
    }
    
    form2 = RegisterForm(form_data2)
    if form2.is_valid():
        print(f"❌ Form validation PASSED (unexpected!)")
    else:
        print(f"✅ Form validation correctly FAILED")
        if 'email' in form2.errors:
            print(f"   Email error: {form2.errors['email']}")
        else:
            print(f"   All errors: {form2.errors}")
else:
    print("No existing users to test with")

# Test 3: Test with case variations
print("\n\nTest 3: Email Case Sensitivity")
print("-" * 80)

# Create a test user
test_user = User.objects.create_user(
    username='casetest123',
    email='CaseTest@cca.edu.ph'  # Mixed case
)
print(f"Created test user with email: {test_user.email}")

# Now try to register with different case
form_data3 = {
    'display_name': 'Case Variation Test',
    'email': 'casetest@cca.edu.ph',  # Different case
    'password1': 'Test@1234!Pass',
    'password2': 'Test@1234!Pass',
    'role': 'Student',
    'studentNumber': '77-7777',
    'course': 'BSCS',
    'section': 1,
    'institute': ''
}

form3 = RegisterForm(form_data3)
if form3.is_valid():
    print(f"❌ Form validation PASSED (case issue!)")
    print(f"   This could cause false positives")
else:
    print(f"✅ Form validation correctly FAILED")
    if 'email' in form3.errors:
        print(f"   Email error: {form3.errors['email']}")

# Cleanup
test_user.delete()
print(f"\n   ✅ Cleaned up test user")

print("\n" + "=" * 80)
