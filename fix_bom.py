#!/usr/bin/env python3
import codecs

# Read and remove BOM
with open('full_backup.json', 'rb') as f:
    content = f.read()

print(f"File size: {len(content)} bytes")
print(f"First 10 bytes: {content[:10]}")

# Remove BOM if present
if content.startswith(codecs.BOM_UTF8):
    content = content[len(codecs.BOM_UTF8):]
    print("✓ UTF-8 BOM removed")
elif content.startswith(b'\xff\xfe'):
    content = content[2:]
    print("✓ UTF-16 LE BOM removed")
elif content.startswith(b'\xfe\xff'):
    content = content[2:]
    print("✓ UTF-16 BE BOM removed")
elif content.startswith(b'\xff'):
    content = content[1:]
    print("✓ Single 0xff byte removed")
else:
    print("✓ No BOM detected")

# Write back
with open('full_backup.json', 'wb') as f:
    f.write(content)

print(f"✓ File fixed - new size: {len(content)} bytes")
