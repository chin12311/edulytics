#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Check for common login issues
"""
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'evaluationWeb.settings')

import django
django.setup()

from django.contrib.auth.models import User
from django.conf import settings
import hashlib

print("=" * 80)
print("LOGIN ISSUE DIAGNOSTIC CHECKLIST")
print("=" * 80)

print("\n[CONFIG] CONFIGURATION:")
print("-" * 80)
print(f"DEBUG: {settings.DEBUG}")
print(f"ALLOWED_HOSTS: {settings.ALLOWED_HOSTS}")
print(f"AUTHENTICATION_BACKENDS: {settings.AUTHENTICATION_BACKENDS}")
print(f"SESSION_ENGINE: {settings.SESSION_ENGINE}")

print("\n[USER] USER DATA:")
print("-" * 80)
user = User.objects.get(email__iexact='Christianbituonon4@gmail.com')
print(f"Username: {user.username!r}")
print(f"Email: {user.email!r}")
print(f"Is Active: {user.is_active}")
print(f"Password Hash: {user.password[:60]}...")
print(f"Password Hash Algorithm: {user.password.split('$')[0]}")

print("\n[PASS] PASSWORD VALIDATION:")
print("-" * 80)
password = 'VNxv76dBIbL@JO7UDqLo'

# Test 1: Direct check
valid = user.check_password(password)
print(f"user.check_password(): {valid}")

# Test 2: Authenticate without request
from django.contrib.auth import authenticate
auth_result = authenticate(username=user.username, password=password)
print(f"authenticate(username=..., password=...): {auth_result is not None}")

# Test 3: Check for common issues
print("\n[ISSUES] POTENTIAL ISSUES:")
print("-" * 80)

issues = []

# Check 1: Empty password
if not password:
    issues.append("ERROR: Password is empty!")

# Check 2: Special characters
if any(c in password for c in ['\n', '\r', '\t', ' ']):
    issues.append("WARNING: Password contains whitespace/special chars")

# Check 3: Username with spaces
if ' ' in user.username:
    print(f"INFO: Username has spaces: '{user.username}'")

# Check 4: Email mismatch
if user.email.lower() != 'christianbituonon4@gmail.com':
    issues.append(f"ERROR: Email mismatch! DB has: {user.email}")

# Check 5: User not active
if not user.is_active:
    issues.append("ERROR: User is not active!")

# Check 6: Password hash looks invalid
if not user.password.startswith('pbkdf2_sha256$'):
    issues.append(f"WARNING: Unexpected password hash type: {user.password[:20]}")

if not issues:
    print("OK: No obvious issues found!")
else:
    for issue in issues:
        print(issue)

print("\n[FORM] FORM TEST:")
print("-" * 80)
from register.forms import LoginForm

form = LoginForm(data={
    'email': 'Christianbituonon4@gmail.com',
    'password': password,
})

if form.is_valid():
    print("OK: LoginForm validation PASSED")
    print(f"   Email (cleaned): {form.cleaned_data['email']!r}")
    print(f"   Password (cleaned): {'*' * len(form.cleaned_data['password'])}")
else:
    print(f"ERROR: LoginForm validation FAILED")
    print(f"   Errors: {form.errors}")

print("\n" + "=" * 80)
print("END OF DIAGNOSTIC")
print("=" * 80)
