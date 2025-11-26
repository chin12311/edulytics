import json
import sys

# Read the complete backup
with open('complete_backup.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# Write with ASCII encoding (will escape special characters)
with open('complete_backup_safe.json', 'w', encoding='ascii') as f:
    json.dump(data, f, ensure_ascii=True, indent=2)

print("Created safe backup file")
