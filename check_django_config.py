#!/usr/bin/env python
"""
Check what Django is actually reading from environment
"""

import os
import sys
import django

# Load .env file fresh
from dotenv import load_dotenv
load_dotenv(override=True)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'evaluationWeb.settings')
django.setup()

from django.conf import settings

print("\n" + "="*80)
print("CHECKING DJANGO EMAIL CONFIGURATION")
print("="*80 + "\n")

print("From evaluationWeb/settings.py:")
print(f"  EMAIL_HOST_USER:    {settings.EMAIL_HOST_USER}")
print(f"  EMAIL_HOST_PASSWORD: {'*' * len(settings.EMAIL_HOST_PASSWORD) if settings.EMAIL_HOST_PASSWORD else 'NOT SET'}")
print(f"  EMAIL_HOST:         {settings.EMAIL_HOST}")
print(f"  EMAIL_PORT:         {settings.EMAIL_PORT}")

print("\nFrom environment variables:")
print(f"  os.getenv('EMAIL_HOST_USER'): {os.getenv('EMAIL_HOST_USER')}")
print(f"  os.getenv('EMAIL_HOST_PASSWORD'): {os.getenv('EMAIL_HOST_PASSWORD')}")

if settings.EMAIL_HOST_PASSWORD == 'vbxlxucdamjcewfn':
    print("\n✅ Django has the correct app password!")
else:
    print(f"\n❌ Django has wrong password!")
    print(f"   Expected: vbxlxucdamjcewfn")
    print(f"   Got: {settings.EMAIL_HOST_PASSWORD}")
