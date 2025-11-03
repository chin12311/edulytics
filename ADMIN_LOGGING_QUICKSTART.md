# 📋 Admin Activity Log - Quick Start Guide

## ✅ Feature Successfully Installed!

The Admin Activity Log feature has been successfully added to your Edulytics system. Here's how to use it:

---

## 🚀 How to View Activity Logs

### Method 1: Admin Control Panel (Recommended)
1. **Login** as an admin user
2. **Navigate** to: http://127.0.0.1:8000/admin-control/
3. **Scroll down** to the "Recent Admin Activity" section
4. View the last 20 activities with:
   - Date & Time
   - Admin who performed the action
   - Action type (with color-coded badges)
   - Description
   - Target user (if applicable)

### Method 2: Django Admin Interface
1. **Login** to Django admin: http://127.0.0.1:8000/admin/
2. **Navigate** to: Main → Admin Activity Logs
3. Features available:
   - Search by admin, user, IP, or description
   - Filter by action type and date
   - Full history (not just last 20)
   - Cannot be manually created (auto-generated only)

---

## 📝 What Gets Logged

### Automatically Logged Actions:

1. **➕ Create Account**
   - When: New user is registered
   - Where: /register/ page
   - Example: "Created new account: john_doe (john@cca.edu.ph) - Role: Student"

2. **✏️ Update Account**
   - When: User profile is edited
   - Where: /update/<user_id>/ page
   - Example: "Updated account for faculty_member (faculty@cca.edu.ph) - Role: Faculty"

3. **🗑️ Delete Account**
   - When: User account is deleted
   - Where: Account management page
   - Example: "Deleted account: old_user (old@cca.edu.ph)"

4. **📌 Assign Section**
   - When: Section(s) assigned to staff/student
   - Where: Section assignment page
   - Example: "Assigned section(s) C101, C102 to faculty_member (Faculty)"

5. **📍 Remove Section**
   - When: Section assignment removed
   - Where: Section management
   - Example: "Removed section C101 from faculty_member"

6. **🚀 Release Evaluation**
   - When: Evaluation forms are released
   - Where: Admin control panel
   - Example: "Released student evaluation form - 1 evaluation(s) activated"

7. **🛑 Unrelease Evaluation**
   - When: Evaluation period ends
   - Where: Admin control panel
   - Example: "Unreleased student evaluation form - 1 evaluation(s) deactivated. Evaluation period ended."

---

## 🧪 Testing the Feature

### Quick Test:
1. **Create a test account**:
   - Go to /register/
   - Fill out the form
   - Submit
   - ✅ This will create an activity log

2. **Check the logs**:
   - Go to /admin-control/
   - Scroll to "Recent Admin Activity"
   - You should see: "Created new account: [username]..."

3. **Try other actions**:
   - Update an account → Check logs
   - Assign a section → Check logs
   - Release evaluation → Check logs

---

## 📊 Log Information Captured

Each log entry contains:
- **Timestamp**: Exact date and time
- **Admin**: Username of who performed the action
- **Action Type**: What was done
- **Description**: Detailed information
- **Target User**: User affected (if applicable)
- **Target Section**: Section involved (if applicable)
- **IP Address**: Network address of admin

---

## 🎨 Color-Coded Action Badges

In the admin control panel, actions are color-coded for easy identification:

- **Green** (➕): Create Account, Release Evaluation
- **Blue** (✏️, 📌): Update Account, Assign Section
- **Yellow** (📍, 🛑): Remove Section, Unrelease Evaluation
- **Red** (🗑️): Delete Account

---

## 🔒 Security Features

✅ **Automatic**: No manual intervention needed
✅ **Immutable**: Logs cannot be edited
✅ **IP Tracking**: Records who and from where
✅ **Fail-safe**: If logging fails, app continues working
✅ **Superuser Protection**: Only superusers can delete logs (in Django admin)

---

## 💡 Tips

1. **Check logs regularly** for unusual activity
2. **Use search** in Django admin to find specific actions
3. **Filter by date** to see activity in a time period
4. **Export data** (future enhancement) for long-term archiving
5. **Monitor IP addresses** for unauthorized access attempts

---

## 🎯 Use Cases

### Accountability
- "Who deleted this account?"
- "When was this section assigned?"

### Troubleshooting
- "What changed before the issue started?"
- "Were any evaluations released on that date?"

### Compliance
- "Show all account deletions this semester"
- "Audit trail for data access"

### Security
- "Which admin made these changes?"
- "Any suspicious IP addresses?"

---

## 📈 Statistics

Currently in your system:
- **Total Users**: 61
- **Total Profiles**: 45
- **Activity Logs**: 0 (will increase as you use the system)

---

## ❓ FAQ

**Q: Can I manually create logs?**
A: No, logs are auto-generated to ensure accuracy.

**Q: Can I edit logs?**
A: No, logs are read-only to maintain integrity.

**Q: Can I delete logs?**
A: Only superusers can delete logs (in Django admin).

**Q: How far back do logs go?**
A: Forever (until manually deleted by superuser).

**Q: Are logs visible to regular users?**
A: No, only admins can see logs.

**Q: What if I delete a user who made changes?**
A: Logs remain (admin field stores username, not just ID).

---

## 🛠️ Technical Details

**Model**: `AdminActivityLog`
**Location**: `main/models.py`
**Helper Function**: `log_admin_activity()` in `main/utils.py`
**Views Updated**: 
- `register/views.py` (RegisterView)
- `main/views.py` (UpdateUser, assign_section, remove_section_assignment, release_student_evaluation, unrelease_student_evaluation)

**Database Table**: `main_adminactivitylog`
**Migration**: `0009_adminactivitylog.py`

---

## 🎉 You're All Set!

The Admin Activity Log feature is now active and logging all administrative actions. 

**Next Steps:**
1. Perform some admin actions (create account, assign section, etc.)
2. Check the logs in /admin-control/
3. Explore the Django admin interface for advanced filtering

**Happy Logging! 📝**

---

*For technical support or questions, refer to ADMIN_ACTIVITY_LOG_FEATURE.md*
