#!/usr/bin/env python3
"""Remove BOM from full_backup.json on AWS"""
import sys

filepath = 'full_backup.json'
with open(filepath, 'rb') as f:
    data = f.read()

original_size = len(data)
print(f"Original size: {original_size} bytes")
print(f"First 20 bytes (hex): {data[:20].hex()}")

# Remove BOM bytes
while data and data[0:1] in (b'\xff', b'\xfe', b'\xef', b'\xbb', b'\xbf'):
    byte = data[0:1]
    data = data[1:]
    print(f"Removed BOM byte: {byte.hex()}")

# Write back
with open(filepath, 'wb') as f:
    f.write(data)

print(f"New size: {len(data)} bytes")
print(f"✓ BOM removed successfully")
