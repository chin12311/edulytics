#!/usr/bin/env python3
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'evaluationWeb.settings')
django.setup()

from django.contrib.auth.models import User
from main.views import DeanProfileSettingsView
import json

# Get jadepuno (the dean with irregular evaluation)
dean = User.objects.get(username='jadepuno')
print(f"Testing data for: {dean.username}")

# Create view instance and call the method
view = DeanProfileSettingsView()
irregular_scores = view.get_irregular_evaluation_scores(dean)

print("\n" + "=" * 60)
print("IRREGULAR SCORES DATA")
print("=" * 60)
print(json.dumps(irregular_scores, indent=2))

print("\n" + "=" * 60)
print("IRREGULAR SCORES JSON (as passed to template)")
print("=" * 60)
irregular_scores_json = json.dumps(irregular_scores)
print(irregular_scores_json)
print("\n")
