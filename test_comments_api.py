#!/usr/bin/env python
"""
Quick test script for the student comments API endpoint
"""
import os
import sys
import json
import django
from django.contrib.auth.models import User
from django.test import Client
from django.urls import reverse

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'evaluationWeb.settings')
django.setup()

# Create a test client
client = Client()

# Get jadepuno user for testing
jadepuno = User.objects.get(username='jadepuno')

print("=" * 60)
print("Testing Student Comments API")
print("=" * 60)

# Test 1: Overall view
print("\n✓ Test 1: Overall Comments (All sections)")
print("-" * 60)

response = client.post(
    '/api/student-comments/',
    data=json.dumps({
        'section_code': 'Overall',
        'section_id': 'overall',
        'timestamp': 1234567890
    }),
    content_type='application/json',
    HTTP_X_CSRFTOKEN=None  # Allow for testing
)

print(f"Status: {response.status_code}")
if response.status_code == 200:
    data = response.json()
    print(f"Comments found: {data.get('total_comments', 0)}")
    print(f"Comments list:")
    for idx, comment in enumerate(data.get('comments', []), 1):
        print(f"  {idx}. {comment[:70]}...")
    print("✅ API returned successfully!")
else:
    print(f"❌ Error: {response.content}")

# Test 2: Peer evaluation
print("\n✓ Test 2: Peer Evaluation Comments")
print("-" * 60)

response = client.post(
    '/api/student-comments/',
    data=json.dumps({
        'section_code': 'Peer Evaluation',
        'section_id': 'peer',
        'timestamp': 1234567890
    }),
    content_type='application/json',
    HTTP_X_CSRFTOKEN=None
)

print(f"Status: {response.status_code}")
if response.status_code == 200:
    data = response.json()
    print(f"Comments found: {data.get('total_comments', 0)}")
    print("✅ API returned successfully!")
else:
    print(f"❌ Error: {response.content}")

print("\n" + "=" * 60)
print("Tests completed!")
print("=" * 60)
