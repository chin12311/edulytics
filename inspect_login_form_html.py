#!/usr/bin/env python
"""
Capture and display the actual HTML form being rendered
"""
import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'evaluationWeb.settings')
django.setup()

from django.test import Client
import re

print("="*80)
print("LOGIN FORM HTML INSPECTION")
print("="*80)

client = Client()
response = client.get('/login/')

if response.status_code == 200:
    html = response.content.decode('utf-8')
    
    # Extract the form
    form_match = re.search(r'<form[^>]*>(.*?)</form>', html, re.DOTALL)
    if form_match:
        form_html = form_match.group(0)
        print("\nFORM HTML:")
        print("-" * 80)
        
        # Find CSRF token
        csrf_match = re.search(r'<input[^>]*csrfmiddlewaretoken[^>]*>', form_html)
        if csrf_match:
            print("CSRF INPUT FOUND:")
            print(f"  {csrf_match.group(0)}")
        else:
            print("❌ CSRF INPUT NOT FOUND IN FORM")
            
        # Find all inputs
        inputs = re.findall(r'<input[^>]*>', form_html)
        print(f"\nALL INPUTS IN FORM ({len(inputs)} total):")
        for idx, inp in enumerate(inputs, 1):
            print(f"  {idx}. {inp}")
            
        # Find all form controls
        print(f"\nFORM STRUCTURE:")
        # Check form action and method
        form_tag_match = re.search(r'<form[^>]*>', form_html)
        if form_tag_match:
            print(f"  Form tag: {form_tag_match.group(0)}")
            
    else:
        print("❌ Could not find <form> tag in HTML")
        
    # Check if there's any JavaScript that might be intercepting form submission
    if '<script' in html:
        print("\n⚠️  JAVASCRIPT DETECTED - Could be intercepting form submission")
        # Find any onclick or form-related JavaScript
        js_match = re.findall(r'<script[^>]*>(.*?)</script>', html, re.DOTALL)
        for js in js_match:
            if 'form' in js.lower() or 'submit' in js.lower():
                print(f"\n  Relevant JavaScript found:")
                print(f"  {js[:200]}")

print("\n" + "="*80)
