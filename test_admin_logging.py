"""
Test script to verify Admin Activity Logging works correctly
Run this after starting the Django server
"""

import os
import django

# Setup Django environment FIRST
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'evaluationWeb.settings')
django.setup()

# NOW import Django models
from django.contrib.auth.models import User
from main.models import AdminActivityLog, UserProfile

def test_logging_feature():
    """Test the admin activity logging feature"""
    
    print("=" * 60)
    print("ADMIN ACTIVITY LOG FEATURE TEST")
    print("=" * 60)
    
    # 1. Check if AdminActivityLog model exists
    print("\n✓ Testing AdminActivityLog model...")
    try:
        log_count = AdminActivityLog.objects.count()
        print(f"  ✅ Model working! Current log count: {log_count}")
    except Exception as e:
        print(f"  ❌ Model error: {e}")
        return
    
    # 2. Display recent logs
    print("\n✓ Fetching recent activity logs...")
    recent_logs = AdminActivityLog.objects.all()[:10]
    
    if recent_logs.exists():
        print(f"  ✅ Found {recent_logs.count()} recent logs:")
        for log in recent_logs:
            print(f"\n  📝 Log ID: {log.id}")
            print(f"     Admin: {log.admin.username if log.admin else 'System'}")
            print(f"     Action: {log.get_action_display()}")
            print(f"     Description: {log.description}")
            print(f"     Target User: {log.target_user.username if log.target_user else 'N/A'}")
            print(f"     IP Address: {log.ip_address or 'N/A'}")
            print(f"     Timestamp: {log.timestamp}")
    else:
        print("  ℹ️  No logs yet. Perform some admin actions to see logs.")
    
    # 3. Test log creation manually (optional)
    print("\n✓ Testing manual log creation...")
    try:
        # Get or create a test admin user
        admin_user = User.objects.filter(is_superuser=True).first()
        
        if admin_user:
            test_log = AdminActivityLog.objects.create(
                admin=admin_user,
                action='update_account',
                description='Test log entry - Manual creation test',
                ip_address='127.0.0.1'
            )
            print(f"  ✅ Test log created successfully! ID: {test_log.id}")
            
            # Clean up test log
            test_log.delete()
            print(f"  ✅ Test log cleaned up")
        else:
            print("  ⚠️  No superuser found. Skipping manual creation test.")
    
    except Exception as e:
        print(f"  ❌ Manual creation error: {e}")
    
    # 4. Show action types
    print("\n✓ Available action types:")
    action_choices = AdminActivityLog.ACTION_CHOICES
    for value, label in action_choices:
        print(f"  • {value}: {label}")
    
    # 5. Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    print(f"Total logs in database: {AdminActivityLog.objects.count()}")
    print(f"Total users in system: {User.objects.count()}")
    print(f"Total user profiles: {UserProfile.objects.count()}")
    
    # Action breakdown
    print("\n📊 Logs by action type:")
    for value, label in action_choices:
        count = AdminActivityLog.objects.filter(action=value).count()
        if count > 0:
            print(f"  {label}: {count}")
    
    print("\n✅ All tests completed!")
    print("=" * 60)

if __name__ == "__main__":
    # Run tests
    test_logging_feature()
