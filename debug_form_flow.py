"""
Debug: Trace exactly what happens during login
"""
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'evaluationWeb.settings')

import django
django.setup()

from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from register.forms import LoginForm

print("=" * 80)
print("EXACT LOGIN FLOW SIMULATION")
print("=" * 80)

# Simulate what happens when form is submitted
email_input = 'Christianbituonon4@gmail.com'
password_input = 'VNxv76dBIbL@JO7UDqLo'

print(f"\n1️⃣ Raw input from form:")
print(f"   Email: {email_input}")
print(f"   Password: {password_input}")

# Create form with the data
form = LoginForm(data={'email': email_input, 'password': password_input})

print(f"\n2️⃣ Form validation:")
if form.is_valid():
    print(f"   ✅ Form is VALID")
    
    # Get cleaned data
    email_cleaned = form.cleaned_data['email']
    password_cleaned = form.cleaned_data['password']
    
    print(f"\n3️⃣ After form cleaning:")
    print(f"   Email: {email_cleaned}")
    print(f"   Password: {password_cleaned}")
    
    # Try user lookup
    print(f"\n4️⃣ User lookup by email (case-insensitive):")
    try:
        user = User.objects.get(email__iexact=email_cleaned)
        print(f"   ✅ Found user: {user.username}")
        print(f"      Username (exact): '{user.username}'")
        print(f"      Username length: {len(user.username)}")
        print(f"      Email in DB: {user.email}")
        
        # Try authentication
        print(f"\n5️⃣ Authenticate with username and password:")
        auth_user = authenticate(username=user.username, password=password_cleaned)
        
        if auth_user:
            print(f"   ✅ authenticate() returned user: {auth_user.username}")
        else:
            print(f"   ❌ authenticate() returned None")
            print(f"\n   🔍 DEBUGGING:")
            print(f"      - Username passed: '{user.username}'")
            print(f"      - Password passed: '{'*' * len(password_cleaned)}'")
            
            # Check if user exists in DB
            user_check = User.objects.filter(username=user.username).first()
            print(f"      - User in DB: {user_check}")
            
            # Try to verify password directly
            print(f"      - User password hash: {user.password[:50]}...")
            password_valid = user.check_password(password_cleaned)
            print(f"      - Password valid (check_password): {password_valid}")
            
    except User.DoesNotExist:
        print(f"   ❌ User NOT found")
        print(f"      Searched for email: '{email_cleaned}'")
        
        # Try to find all users
        all_users = User.objects.all()
        print(f"      Total users in DB: {all_users.count()}")
        print(f"      All emails:")
        for u in all_users[:5]:
            print(f"         - {u.email}")
else:
    print(f"   ❌ Form is INVALID")
    print(f"   Errors: {form.errors}")

print("\n" + "=" * 80)
