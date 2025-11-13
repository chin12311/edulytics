#!/usr/bin/env python
"""
Direct data migration script from SQLite to MySQL
"""
import os
import django
import json

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'evaluationWeb.settings')
django.setup()

from django.core.management import call_command
from django.core.serializers import deserialize

# Load the JSON fixture
print("Loading fixture file...")
with open('fixtures_from_sqlite.json', 'r', encoding='utf-8') as f:
    fixture_data = json.load(f)

print(f"Loaded {len(fixture_data)} objects from fixture")

# Deserialize and save objects
objects_to_save = list(deserialize('json', json.dumps(fixture_data)))
print(f"Deserialized {len(objects_to_save)} objects")

# Disable foreign key checks while loading
from django.db import connection
with connection.cursor() as cursor:
    cursor.execute("SET FOREIGN_KEY_CHECKS=0;")

# Save each object
saved_count = 0
for obj in objects_to_save:
    try:
        obj.save()
        saved_count += 1
        if saved_count % 10 == 0:
            print(f"Saved {saved_count}/{len(objects_to_save)} objects...")
    except Exception as e:
        print(f"Error saving {obj.object.__class__.__name__} {obj.object.pk}: {e}")
        
# Re-enable foreign key checks
with connection.cursor() as cursor:
    cursor.execute("SET FOREIGN_KEY_CHECKS=1;")

print(f"\n✅ Successfully saved {saved_count}/{len(objects_to_save)} objects")

# Verify
from django.contrib.auth.models import User
from main.models import UserProfile

user_count = User.objects.count()
profile_count = UserProfile.objects.count()
print(f"Users in MySQL: {user_count}")
print(f"Profiles in MySQL: {profile_count}")
