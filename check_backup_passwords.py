import json

data = json.load(open('users_only.json'))
users = [u for u in data if u['model'] == 'auth.user']

print("=" * 80)
print(f"First 5 users in backup and their password hashes:")
print("=" * 80)

for u in users[:5]:
    print(f"\nUsername: {u['fields']['username']}")
    print(f"Password: {u['fields']['password'][:80]}")
