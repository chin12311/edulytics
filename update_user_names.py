import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'evaluationWeb.settings')
django.setup()

from django.contrib.auth.models import User
from main.models import UserProfile

print("Updating User first_name and last_name from UserProfile display_name...")
print("=" * 70)

updated_count = 0
total_users = User.objects.all().count()

for user in User.objects.all():
    try:
        profile = user.userprofile
        display_name = profile.display_name or user.username
        
        # Split display_name into first_name and last_name
        name_parts = display_name.strip().split(None, 1)  # Split on first space
        first_name = name_parts[0] if name_parts else display_name
        last_name = name_parts[1] if len(name_parts) > 1 else ''
        
        # Update user if names are different
        if user.first_name != first_name or user.last_name != last_name:
            old_full_name = user.get_full_name() or user.username
            user.first_name = first_name
            user.last_name = last_name
            user.save()
            new_full_name = user.get_full_name()
            print(f"✅ {user.username}: '{old_full_name}' → '{new_full_name}'")
            updated_count += 1
    except UserProfile.DoesNotExist:
        print(f"⚠️  {user.username}: No profile found, skipping")
        continue
    except Exception as e:
        print(f"❌ {user.username}: Error - {e}")
        continue

print("=" * 70)
print(f"✅ Updated {updated_count} out of {total_users} users")
print(f"✅ {total_users - updated_count} users already had correct names")
