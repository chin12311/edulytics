# Admin Activity Log Feature

## Overview
The Admin Activity Log feature automatically tracks all major administrative actions performed in the Edulytics system. This provides a complete audit trail for accountability and troubleshooting.

## Tracked Activities

### 1. **Create Account** (`create_account`)
- Triggered when: A new user account is created via the registration form
- Records: Admin who created it, new user details, role
- Location: `/register/` (RegisterView)

### 2. **Update Account** (`update_account`)
- Triggered when: An existing user account is modified
- Records: Admin who updated it, target user, changes made
- Location: `/update/<user_id>/` (UpdateUser view)

### 3. **Delete Account** (`delete_account`)
- Triggered when: A user account is deleted
- Records: Admin who deleted it, deleted user's username and email
- Location: `/delete/<user_id>/` (UpdateUser.delete)

### 4. **Assign Section** (`assign_section`)
- Triggered when: Section(s) are assigned to a user
- Records: Admin, target user, section codes assigned
- Location: `/assign-section/<user_id>/` (assign_section view)

### 5. **Remove Section** (`remove_section`)
- Triggered when: A section assignment is removed
- Records: Admin, target user, section removed
- Location: `/remove-section/<assignment_id>/` (remove_section_assignment view)

### 6. **Release Evaluation** (`release_evaluation`)
- Triggered when: Evaluation forms are released to students
- Records: Admin, number of evaluations released
- Location: `/release-student-evaluation/` (release_student_evaluation view)

### 7. **Unrelease Evaluation** (`unrelease_evaluation`)
- Triggered when: Evaluation forms are unreleased (evaluation period ends)
- Records: Admin, number of evaluations deactivated
- Location: `/unrelease-student-evaluation/` (unrelease_student_evaluation view)

## Database Schema

### AdminActivityLog Model
```python
class AdminActivityLog(models.Model):
    admin = ForeignKey(User)              # Who performed the action
    action = CharField(max_length=50)      # Type of action (see choices above)
    target_user = ForeignKey(User)         # User affected by the action (nullable)
    target_section = ForeignKey(Section)   # Section affected (nullable)
    description = TextField()              # Detailed description
    timestamp = DateTimeField()            # When the action occurred
    ip_address = GenericIPAddressField()   # IP address of the admin
```

## Viewing Activity Logs

### 1. Admin Control Panel
- Navigate to: `/admin-control/`
- Shows: Last 20 activities in a table format
- Displays:
  - Date & Time
  - Admin username
  - Action type with color-coded badges
  - Description
  - Target user (if applicable)

### 2. Django Admin Interface
- Navigate to: `/admin/main/adminactivitylog/`
- Features:
  - Full searchable log history
  - Filter by action type and date
  - Search by admin, target user, IP address, or description
  - Read-only (cannot be manually created)
  - Only superusers can delete logs

## Usage Examples

### Example 1: Account Creation
```
Timestamp: Oct 31, 2025 10:30 AM
Admin: admin_user
Action: Create Account
Description: Created new account: john_doe (john@cca.edu.ph) - Role: Student
Target User: john_doe
IP: 127.0.0.1
```

### Example 2: Section Assignment
```
Timestamp: Oct 31, 2025 11:15 AM
Admin: admin_user
Action: Assign Section
Description: Assigned section(s) C101, C102 to faculty_member (Faculty)
Target User: faculty_member
IP: 127.0.0.1
```

### Example 3: Evaluation Release
```
Timestamp: Oct 31, 2025 02:00 PM
Admin: admin_user
Action: Release Evaluation
Description: Released student evaluation form - 1 evaluation(s) activated
Target User: None
IP: 127.0.0.1
```

## Security Features

1. **Automatic Logging**: All actions are logged automatically without admin intervention
2. **IP Address Tracking**: Records the IP address of the admin performing the action
3. **Immutable Records**: Logs cannot be edited through the UI
4. **Deletion Protection**: Only superusers can delete logs (in Django admin)
5. **Silent Failure**: If logging fails, the action still proceeds (doesn't break app)

## Benefits

✅ **Accountability**: Know who did what and when
✅ **Audit Trail**: Complete history of administrative changes
✅ **Troubleshooting**: Identify when issues were introduced
✅ **Compliance**: Meet institutional audit requirements
✅ **Security**: Track unauthorized access attempts
✅ **Analytics**: Understand admin workflow patterns

## Technical Implementation

### Helper Function
```python
# utils.py
def log_admin_activity(request, action, description, target_user=None, target_section=None):
    """Log admin activities with IP tracking"""
    AdminActivityLog.objects.create(
        admin=request.user,
        action=action,
        target_user=target_user,
        target_section=target_section,
        description=description,
        ip_address=get_client_ip(request)
    )
```

### Usage in Views
```python
# After creating an account
log_admin_activity(
    request=request,
    action='create_account',
    description=f"Created new account: {user.username} ({user.email}) - Role: {role}",
    target_user=user
)

# After assigning sections
log_admin_activity(
    request=request,
    action='assign_section',
    description=f"Assigned section(s) {sections} to {user.username}",
    target_user=user
)
```

## Migration

Run these commands to set up the database:
```bash
python manage.py makemigrations
python manage.py migrate
```

This creates the `main_adminactivitylog` table in your database.

## Future Enhancements (Optional)

1. **Export Logs**: Add ability to export logs to CSV/PDF
2. **Email Notifications**: Alert on critical actions (account deletions)
3. **Log Retention Policy**: Auto-delete logs older than X months
4. **Advanced Filtering**: Filter by date range, multiple action types
5. **Dashboard Charts**: Visualize activity trends over time
6. **User-specific Logs**: Show all actions related to a specific user

## Support

For questions or issues related to the Admin Activity Log feature, contact your system administrator or refer to the Django documentation.

---

**Last Updated**: October 31, 2025
**Version**: 1.0
**Status**: Production Ready ✅
