#!/usr/bin/env python
"""
Backup all data from local MySQL database to JSON file for AWS deployment
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'evaluationWeb.settings')
django.setup()

from django.core.management import call_command

# Dump all data to JSON file
print("Backing up all database data...")
with open('evaluation_backup.json', 'w') as f:
    call_command('dumpdata', stdout=f)

print("Backup complete: evaluation_backup.json")
print("File size:", os.path.getsize('evaluation_backup.json'), "bytes")
