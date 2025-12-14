from django.contrib.auth.models import User
users = User.objects.filter(username__icontains='ilao')
print(f'Found {users.count()} users')
for u in users:
    if hasattr(u, 'userprofile'):
        print(f'{u.username} - {u.userprofile.role} - Section: {u.userprofile.section}')
