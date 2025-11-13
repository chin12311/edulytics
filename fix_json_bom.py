import codecs

# Read and remove BOM
with open('full_backup.json', 'rb') as f:
    content = f.read()

# Remove BOM if present
if content.startswith(codecs.BOM_UTF8):
    content = content[len(codecs.BOM_UTF8):]

# Write back without BOM
with open('full_backup.json', 'wb') as f:
    f.write(content)

print("BOM removed from full_backup.json")
