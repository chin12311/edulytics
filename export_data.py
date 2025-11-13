#!/usr/bin/env python
import os
import django
import sys

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'evaluationWeb.settings')
os.environ['PYTHONIOENCODING'] = 'utf-8'

django.setup()

from django.core.management import call_command
import io

# Redirect stdout to capture output
output = io.StringIO()
call_command('dumpdata', stdout=output)

# Write to file with proper encoding
with open('fixtures_from_sqlite.json', 'w', encoding='utf-8') as f:
    f.write(output.getvalue())

print("Data exported successfully to fixtures_from_sqlite.json")
