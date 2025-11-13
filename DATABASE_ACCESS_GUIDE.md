# 📊 Database Access Guide

**Date**: November 9, 2025  
**Database**: MySQL 9.5  
**Status**: Ready for access

---

## 🔑 Your Database Credentials

```
Host: localhost
Port: 3306
Database: evaluation
Username: eval_user
Password: !eETXiuo4LHxeu6M4#sz
```

---

## 🛠️ Method 1: Command Line (Easiest)

### Access MySQL Command Line

**Open PowerShell and run:**

```powershell
& "C:\Program Files\MySQL\MySQL Server 9.5\bin\mysql.exe" -u eval_user -p"!eETXiuo4LHxeu6M4#sz" -h localhost evaluation
```

**You'll see:**
```
Welcome to the MySQL monitor...
mysql>
```

### Basic Commands

Once in MySQL, try these:

```sql
-- Show all tables
SHOW TABLES;

-- Count total users
SELECT COUNT(*) as total_users FROM auth_user;

-- Count total evaluations
SELECT COUNT(*) as evaluations FROM main_evaluation;

-- Count total evaluation responses
SELECT COUNT(*) as responses FROM main_evaluationresponse;

-- Exit MySQL
EXIT;
```

---

## 🛠️ Method 2: Django Shell (For Python/Django)

### Access via Django

**Open PowerShell:**

```powershell
python manage.py shell
```

**Then run Python commands:**

```python
# Import models
from django.contrib.auth.models import User
from main.models import Evaluation, EvaluationResponse

# Count users
print(f"Total users: {User.objects.count()}")

# List all users
for user in User.objects.all()[:10]:
    print(f"  - {user.username} ({user.email})")

# Count evaluations
print(f"Total evaluations: {Evaluation.objects.count()}")

# Count responses
print(f"Total responses: {EvaluationResponse.objects.count()}")

# Exit shell
exit()
```

---

## 🛠️ Method 3: GUI Tools (Recommended for Browsing)

### Option A: MySQL Workbench (Professional)

1. **Download**: https://dev.mysql.com/downloads/workbench/
2. **Install**: Run the installer
3. **Open Workbench**
4. **Click**: "MySQL Connections" → "+" button
5. **Enter**:
   - Connection Name: `Evaluation DB`
   - Hostname: `localhost`
   - Port: `3306`
   - Username: `eval_user`
   - Password: (click "Store in Vault" and enter `!eETXiuo4LHxeu6M4#sz`)
6. **Test Connection** → Click "OK"
7. **Browse** your database visually!

### Option B: HeidiSQL (Lightweight & Free)

1. **Download**: https://www.heidisql.com/download.php
2. **Install**: Run the installer
3. **Open HeidiSQL**
4. **New Connection**:
   - Host/IP: `localhost`
   - User: `eval_user`
   - Password: `!eETXiuo4LHxeu6M4#sz`
   - Port: `3306`
5. **Open** → Navigate your database
6. **Query Editor** → Write SQL queries

### Option C: DBeaver (Powerful IDE)

1. **Download**: https://dbeaver.io/download/
2. **Install**: Run the installer
3. **Open DBeaver**
4. **Database** → **New Database Connection**
5. **Select**: MySQL → **Next**
6. **Enter**:
   - Server Host: `localhost`
   - Port: `3306`
   - Database: `evaluation`
   - Username: `eval_user`
   - Password: `!eETXiuo4LHxeu6M4#sz`
7. **Test Connection** → **Finish**
8. **Browse** and **Query** your data!

---

## 📋 Common Queries

### Users Table

```sql
-- See all users
SELECT id, username, email, is_staff, is_superuser, is_active FROM auth_user;

-- Find a specific user
SELECT * FROM auth_user WHERE username = 'Christian Bitu-onon1';

-- Count users by role
SELECT is_staff, is_superuser, COUNT(*) FROM auth_user GROUP BY is_staff, is_superuser;
```

### Evaluations

```sql
-- See all evaluations
SELECT * FROM main_evaluation;

-- See evaluation details with count
SELECT 
  e.id, 
  e.title, 
  e.description, 
  COUNT(er.id) as response_count
FROM main_evaluation e
LEFT JOIN main_evaluationresponse er ON e.id = er.evaluation_id
GROUP BY e.id;
```

### Evaluation Responses

```sql
-- See all responses
SELECT 
  r.id, 
  r.evaluation_id, 
  u.username as evaluator,
  r.submitted_at
FROM main_evaluationresponse r
JOIN auth_user u ON r.evaluator_id = u.id
ORDER BY r.submitted_at DESC;

-- Count responses by user
SELECT 
  u.username, 
  COUNT(r.id) as response_count
FROM main_evaluationresponse r
JOIN auth_user u ON r.evaluator_id = u.id
GROUP BY u.id
ORDER BY response_count DESC;
```

### Sections

```sql
-- See all sections
SELECT * FROM main_section LIMIT 20;

-- Count sections by year
SELECT year_level, COUNT(*) FROM main_section GROUP BY year_level;
```

### User Profiles

```sql
-- See user profiles
SELECT 
  u.username, 
  p.display_name, 
  p.role,
  p.department
FROM auth_user u
LEFT JOIN main_userprofile p ON u.id = p.user_id
LIMIT 20;
```

---

## 🔍 Viewing Database Structure

### See All Tables

```sql
SHOW TABLES;
```

**Output:**
```
+----------------------------+
| Tables_in_evaluation       |
+----------------------------+
| auth_group                 |
| auth_group_permissions     |
| auth_permission            |
| auth_user                  |
| auth_user_groups           |
| auth_user_user_permissions |
| django_admin_log           |
| django_content_type        |
| django_migrations          |
| django_session             |
| main_adminactivitylog      |
| main_airecommendation      |
| main_coordinator           |
| main_evaluation            |
| main_evaluationcomment     |
| main_evaluationfailurelog  |
| main_evaluationperiod      |
| main_evaluationresponse    |
| main_evaluationresult      |
| main_section               |
| main_sectionassignment     |
| main_userprofile           |
+----------------------------+
```

### See Table Structure

```sql
-- Describe a table
DESCRIBE auth_user;

-- Or use SHOW
SHOW COLUMNS FROM auth_user;

-- See indexes
SHOW INDEXES FROM main_evaluationresponse;
```

---

## 📊 Database Statistics

### Quick Stats

```sql
-- Total records in each table
SELECT 'auth_user' as table_name, COUNT(*) as count FROM auth_user
UNION
SELECT 'main_evaluation', COUNT(*) FROM main_evaluation
UNION
SELECT 'main_evaluationresponse', COUNT(*) FROM main_evaluationresponse
UNION
SELECT 'main_section', COUNT(*) FROM main_section
UNION
SELECT 'main_userprofile', COUNT(*) FROM main_userprofile;
```

### Database Size

```sql
-- Check database size
SELECT 
  SUM(round(((data_length + index_length) / 1024 / 1024), 2)) AS 'Size (MB)'
FROM information_schema.TABLES 
WHERE table_schema = 'evaluation';

-- Check individual tables
SELECT 
  table_name,
  round(((data_length + index_length) / 1024 / 1024), 2) AS 'Size (MB)'
FROM information_schema.TABLES 
WHERE table_schema = 'evaluation'
ORDER BY (data_length + index_length) DESC;
```

---

## 💾 Backing Up Your Database

### Command Line Backup

```powershell
# Backup to file
mysqldump -u eval_user -p"!eETXiuo4LHxeu6M4#sz" evaluation > backup_$(date -u +%Y%m%d_%H%M%S).sql

# Or use this for Windows
mysqldump -u eval_user -p"!eETXiuo4LHxeu6M4#sz" evaluation > backup.sql
```

### Restore from Backup

```powershell
# Restore from file
mysql -u eval_user -p"!eETXiuo4LHxeu6M4#sz" evaluation < backup.sql
```

---

## 🔧 Useful Database Operations

### Add a New User (from command line)

```sql
-- Insert via MySQL
INSERT INTO auth_user (username, email, password, is_active) 
VALUES ('newuser', 'newuser@example.com', 'pbkdf2_sha256$600000$...', 1);
```

### Update User Status

```sql
-- Disable a user
UPDATE auth_user SET is_active = 0 WHERE username = 'username';

-- Enable a user
UPDATE auth_user SET is_active = 1 WHERE username = 'username';

-- Make someone an admin
UPDATE auth_user SET is_staff = 1, is_superuser = 1 WHERE username = 'username';
```

### Query Data with Filtering

```sql
-- Find inactive users
SELECT * FROM auth_user WHERE is_active = 0;

-- Find staff members
SELECT * FROM auth_user WHERE is_staff = 1;

-- Find evaluations from last 30 days
SELECT * FROM main_evaluation 
WHERE created_at >= DATE_SUB(NOW(), INTERVAL 30 DAY);
```

---

## 🚀 Advanced: Python/Django Database Access

### From Python Script

Create a file `query_db.py`:

```python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'evaluationWeb.settings')
django.setup()

from django.contrib.auth.models import User
from main.models import Evaluation, EvaluationResponse

# Query users
print("=== USERS ===")
users = User.objects.all()
print(f"Total: {users.count()}")
for user in users[:5]:
    print(f"  - {user.username} ({user.email})")

# Query evaluations
print("\n=== EVALUATIONS ===")
evaluations = Evaluation.objects.all()
print(f"Total: {evaluations.count()}")
for eval in evaluations:
    responses = EvaluationResponse.objects.filter(evaluation=eval).count()
    print(f"  - {eval.title}: {responses} responses")

# Query responses
print("\n=== EVALUATION RESPONSES ===")
responses = EvaluationResponse.objects.all().select_related('evaluator')
print(f"Total: {responses.count()}")
for resp in responses[:5]:
    print(f"  - {resp.evaluator.username} (ID: {resp.id})")
```

**Run it:**
```powershell
python query_db.py
```

---

## 📌 Quick Reference

### Most Used Ports
- **MySQL**: 3306
- **Django**: 8000

### Connection String for Tools
```
mysql://eval_user:!eETXiuo4LHxeu6M4#sz@localhost:3306/evaluation
```

### File Locations
```
MySQL: C:\Program Files\MySQL\MySQL Server 9.5\
Django: c:\Users\ADMIN\eval\evaluation\
Database: evaluation
```

---

## 🆘 Troubleshooting

### "Access denied for user 'eval_user'"

**Check your credentials:**
```powershell
mysql -u eval_user -p
# Enter password: !eETXiuo4LHxeu6M4#sz
```

### "Can't connect to MySQL server"

**Verify MySQL is running:**
```powershell
Get-Service | findstr -i mysql
```

**If stopped, start it:**
```powershell
Start-Service MySQL95
```

### "Unknown database 'evaluation'"

**List all databases:**
```sql
SHOW DATABASES;
```

**Verify database exists:**
```sql
CREATE DATABASE IF NOT EXISTS evaluation CHARACTER SET utf8mb4;
```

---

## 🎯 Summary

| Method | Best For | Ease | Speed |
|--------|----------|------|-------|
| **Command Line** | Quick queries, scripting | ⭐⭐⭐ | ⭐⭐⭐ |
| **Django Shell** | Python data, app logic | ⭐⭐⭐ | ⭐⭐ |
| **MySQL Workbench** | Professional admin | ⭐⭐ | ⭐⭐⭐ |
| **HeidiSQL** | Quick browsing | ⭐⭐⭐ | ⭐⭐⭐ |
| **DBeaver** | Full-featured IDE | ⭐ | ⭐⭐ |
| **Python Script** | Automation, exports | ⭐⭐ | ⭐⭐ |

---

## ✅ Next Steps

### Immediate
1. Try accessing via command line
2. Run a simple query (SELECT * FROM auth_user)
3. Verify data is there

### Soon
1. Download a GUI tool (HeidiSQL recommended)
2. Learn basic SQL queries
3. Explore your database structure

### Later
1. Set up automated backups
2. Create read-only users for reporting
3. Set up monitoring and alerts

---

**Your database is ready to access! Choose your method above and start exploring! 🚀**

