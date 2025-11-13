#!/usr/bin/env python
"""
Test script to verify static files are correctly configured and accessible
"""

import os
import sys
import django
from pathlib import Path

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'evaluationWeb.settings')
sys.path.insert(0, str(Path(__file__).parent))
django.setup()

from django.conf import settings
from django.core.management import call_command

print("=" * 70)
print("STATIC FILES CONFIGURATION TEST")
print("=" * 70)

# Test 1: Check DEBUG setting
print("\n✓ DEBUG Setting")
print(f"  DEBUG = {settings.DEBUG}")

# Test 2: Check STATIC_URL
print("\n✓ STATIC_URL")
print(f"  STATIC_URL = {settings.STATIC_URL}")

# Test 3: Check STATIC_ROOT
print("\n✓ STATIC_ROOT")
print(f"  STATIC_ROOT = {settings.STATIC_ROOT}")
print(f"  Exists: {settings.STATIC_ROOT.exists() if hasattr(settings.STATIC_ROOT, 'exists') else os.path.exists(settings.STATIC_ROOT)}")

# Test 4: Check STATICFILES_DIRS
print("\n✓ STATICFILES_DIRS")
if hasattr(settings, 'STATICFILES_DIRS'):
    for idx, dir_path in enumerate(settings.STATICFILES_DIRS):
        exists = dir_path.exists() if hasattr(dir_path, 'exists') else os.path.exists(dir_path)
        print(f"  [{idx}] {dir_path} - Exists: {exists}")
else:
    print("  Not configured")

# Test 5: Check if images exist in STATIC_ROOT
print("\n✓ Images in STATIC_ROOT")
static_root = settings.STATIC_ROOT
img_dir = Path(static_root) / 'img' if isinstance(static_root, str) else static_root / 'img'
if img_dir.exists():
    images = list(img_dir.glob('*.png')) + list(img_dir.glob('*.jpg'))
    print(f"  Found {len(images)} image files:")
    for img in sorted(images)[:5]:
        print(f"    - {img.name}")
    if len(images) > 5:
        print(f"    ... and {len(images) - 5} more")
else:
    print(f"  ❌ Image directory not found: {img_dir}")

# Test 6: Test findstatic command
print("\n✓ Testing findstatic command")
try:
    from django.contrib.staticfiles.finders import get_finders
    from django.contrib.staticfiles import finders
    
    phoenix_bg = finders.find('img/phoenix-background.png')
    if phoenix_bg:
        print(f"  ✓ Found phoenix-background.png at: {phoenix_bg}")
    else:
        print(f"  ❌ Could not find phoenix-background.png")
        
    cca_logo = finders.find('img/cca-logo.png')
    if cca_logo:
        print(f"  ✓ Found cca-logo.png at: {cca_logo}")
    else:
        print(f"  ❌ Could not find cca-logo.png")
        
except Exception as e:
    print(f"  Error: {e}")

# Test 7: URL configuration
print("\n✓ URL Configuration")
from django.urls import get_resolver
from django.conf.urls.static import static
print(f"  STATIC_URL routes configured: {any('static' in str(pattern.pattern) for pattern in get_resolver().url_patterns)}")

print("\n" + "=" * 70)
print("NEXT STEPS:")
print("=" * 70)
print("""
1. Run the development server:
   python manage.py runserver
   
2. Visit the site in your browser:
   http://127.0.0.1:8000
   
3. If images still don't show:
   - Open browser DevTools (F12)
   - Go to Network tab
   - Reload the page
   - Look for static file requests with 404 errors
   - Check the requested URL path
""")

print("\n" + "=" * 70)
