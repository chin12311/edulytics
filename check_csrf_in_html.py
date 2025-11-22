#!/usr/bin/env python
"""
Check what CSRF token is being rendered in the HTML
"""
import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'evaluationWeb.settings')
django.setup()

from django.test import Client
from django.urls import reverse
import re

print("="*80)
print("CSRF TOKEN IN HTML ANALYSIS")
print("="*80)

client = Client()
response = client.get(reverse('register:login'))

# Find the CSRF token in HTML
html = response.content.decode('utf-8')

# Search for csrfmiddlewaretoken in the HTML
csrf_pattern = r'name=["\']csrfmiddlewaretoken["\'].*?value=["\']([^"\']+)["\']'
match = re.search(csrf_pattern, html, re.DOTALL)

if match:
    csrf_value = match.group(1)
    print(f"\nOK: CSRF token found in HTML:")
    print(f"   Value: {csrf_value[:20]}...")
    print(f"   Length: {len(csrf_value)} chars")
else:
    print(f"\nERROR: CSRF token NOT found in HTML with pattern")
    
    # Try alternative pattern
    if 'csrfmiddlewaretoken' in html:
        print(f"   But 'csrfmiddlewaretoken' appears in HTML")
        # Find the section
        idx = html.find('csrfmiddlewaretoken')
        print(f"   Context: ...{html[max(0,idx-50):idx+100]}...")
    else:
        print(f"   'csrfmiddlewaretoken' does NOT appear in HTML at all!")

# Print the form section
form_start = html.find('<form action')
form_end = html.find('</form>') + 7
if form_start != -1 and form_end > form_start:
    form_html = html[form_start:form_end]
    print(f"\nForm HTML (first 500 chars):")
    print(form_html[:500])
    print("...(truncated)")

print("\n" + "="*80)
