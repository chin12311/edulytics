from django.contrib.auth.models import User
from main.models import UserProfile, Role

print("=" * 80)
print("ALL FACULTY ACCOUNTS")
print("=" * 80)

faculty_profiles = UserProfile.objects.filter(role=Role.FACULTY)
print(f"\nTotal faculty accounts: {faculty_profiles.count()}\n")

for profile in faculty_profiles:
    user = profile.user
    print(f"Username: {user.username}")
    print(f"Name: {user.first_name} {user.last_name}")
    print(f"Email: {user.email}")
    print(f"Institute: {profile.institute}")
    print("-" * 40)

print("=" * 80)
