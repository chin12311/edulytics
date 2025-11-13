#!/usr/bin/env python3
"""Export complete backup without encoding issues"""
import json
import subprocess
import sys

# Use Django to generate JSON, then save it properly
result = subprocess.run([
    sys.executable, 'manage.py', 'dumpdata',
    'auth.user', 'auth.group', 'main.userprofile', 
    'main.evaluation', 'main.evaluationresponse',
    'main.evaluationresult', 'main.evaluationhistory',
    'main.airecommendation',
    '--indent', '2'
], capture_output=True, text=True)

if result.returncode != 0:
    print(f"Error: {result.stderr}")
    sys.exit(1)

# Write with proper UTF-8 encoding, no BOM
data = result.stdout
with open('complete_backup.json', 'w', encoding='utf-8-sig') as f:
    f.write(data)

# Verify it's valid JSON
try:
    json.loads(data)
    print(f"✓ Valid JSON exported ({len(data)} bytes)")
except Exception as e:
    print(f"Error: {e}")
    sys.exit(1)
