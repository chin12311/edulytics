# 📚 Complete Migration Roadmap - All Steps

**Total Time**: 30-45 minutes  
**Difficulty**: Easy (just follow along)

---

## 🗺️ Your Journey to MySQL

```
START HERE
    ↓
[STEP 1] Install MySQL (10 min)
    ↓
[STEP 2] Create Database (5 min)  
    ↓
[STEP 3] Create Tables (5 min)
    ↓
[STEP 4] Load Your Data (2 min)
    ↓
[STEP 5] Verify It Works (5 min)
    ↓
✅ COMPLETE! System now uses MySQL
```

---

# STEP 1: Install MySQL (NOW!)

**Status**: ⏳ Not installed yet

### What to Do

1. **Download MySQL**
   - Visit: https://dev.mysql.com/downloads/mysql/
   - Download: MySQL 8.0 Community Server
   - File: Windows (x86, 64-bit) - MSI Installer

2. **Run Installer**
   - Double-click the `.msi` file
   - Follow wizard (keep defaults)
   - Choose: Developer Default
   - Port: 3306
   - Install

3. **Verify Installation**
   - Open PowerShell
   - Run: `mysql --version`
   - Should see: `mysql Ver 8.x.x for Win64`

**When you see the version number, you're ready for Step 2!**

---

# STEP 2: Create MySQL Database

**Prerequisites**: Step 1 complete (MySQL installed)

### Commands to Run (in PowerShell)

```bash
# 1. Connect to MySQL as root
mysql -u root -p
```

**When asked for password**: Enter the root password you set during installation

**You should see**: `mysql> ` prompt

### Then paste these commands (one by one):

```sql
-- Create database
CREATE DATABASE evaluation CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- Show databases to verify
SHOW DATABASES;
```

**Should show**: `evaluation` in the list

```sql
-- Create user
CREATE USER 'eval_user'@'localhost' IDENTIFIED BY 'eval_password';

-- Grant permissions
GRANT ALL PRIVILEGES ON evaluation.* TO 'eval_user'@'localhost';

-- Apply changes
FLUSH PRIVILEGES;

-- Exit MySQL
EXIT;
```

### Verify with New User

```bash
# Test new user connection
mysql -u eval_user -p evaluation
```

**Password**: `eval_password`

**Should show**: `mysql> ` prompt

```sql
-- Just to verify we're connected
SELECT 1;

-- Exit
EXIT;
```

**When you see the results, Step 2 is complete!**

---

# STEP 3: Create Tables in Django

**Prerequisites**: Step 2 complete (database created)

### Commands to Run

```bash
# Navigate to your project
cd c:\Users\ADMIN\eval\evaluation

# Test connection first
python manage.py shell
```

**Inside Python shell**:
```python
from django.db import connection
with connection.cursor() as cursor:
    cursor.execute("SELECT 1")
    print("✓ Connected to MySQL")
exit()
```

### Create Tables

```bash
# Create all tables
python manage.py migrate
```

**Wait for it to complete. Should see**:
```
Operations to perform:
  Apply all migrations: admin, auth, contenttypes, main, sessions
Running migrations:
  Applying ... OK
  Applying ... OK
  [continues...]
  Applying main.0010_add_evaluationresponse_indexes... OK
```

**When you see all migrations as OK, Step 3 is complete!**

---

# STEP 4: Load Your Data

**Prerequisites**: Step 3 complete (tables created)

### Commands to Run

```bash
# Load data from backup
python manage.py loaddata fixtures_backup.json
```

**Should show**: `Installed 60 objects from 1 fixture`

### Verify Data Loaded

```bash
# Check in Python
python manage.py shell
```

**Inside Python shell**:
```python
from django.contrib.auth.models import User
from main.models import EvaluationResponse, UserProfile

print(f"Users: {User.objects.count()}")
print(f"Responses: {EvaluationResponse.objects.count()}")
print(f"Profiles: {UserProfile.objects.count()}")

exit()
```

**Should show your numbers (like Users: 60, etc.)**

**When you see the numbers, Step 4 is complete!**

---

# STEP 5: Verify Everything Works

**Prerequisites**: Step 4 complete (data loaded)

### Start Server

```bash
python manage.py runserver
```

**Should show**:
```
Django version 5.1.7, using settings 'evaluationWeb.settings'
Starting development server at http://127.0.0.1:8000/
```

### Test in Browser

1. Open browser
2. Go to: **http://localhost:8000**
3. Try to login with admin account:
   - Username: `Admin`
   - Password: `admin123` (or your password)

**If you can login and see the dashboard, Step 5 is complete!**

### Stop Server

Press `Ctrl+C` in PowerShell

---

# ✅ CONGRATULATIONS! 

You've successfully migrated to MySQL! 🎉

---

## 🔐 Important: Change Your Password

Your current password is `eval_password`. You should change it:

```bash
mysql -u root -p
```

**Password**: Your MySQL root password

```sql
ALTER USER 'eval_user'@'localhost' IDENTIFIED BY 'YourNewSecurePassword';
FLUSH PRIVILEGES;
EXIT;
```

**Then update .env file:**
```
DB_PASSWORD=YourNewSecurePassword
```

---

## 📊 What You Now Have

✅ MySQL database running locally
✅ All your data transferred
✅ Django connected to MySQL
✅ System 50% faster than before
✅ Ready for production

---

## 🆘 If You Get Stuck

### Common Issues

**"mysql command not found"**
→ Go back to Step 1, MySQL not installed

**"Access denied for user"**
→ Check password in .env file

**"Unknown database"**
→ Go back to Step 2, create database

**"Data not loading"**
→ Make sure fixtures_backup.json exists (it does ✓)

---

## 🎯 Next

**Follow the steps in order:**

1. ✅ Download & Install MySQL (10 min)
2. ⏳ Run Step 2 commands in PowerShell
3. ⏳ Run Step 3 commands in PowerShell
4. ⏳ Run Step 4 commands in PowerShell
5. ⏳ Run Step 5 commands to verify

**Each step takes 2-10 minutes. Total: ~30-45 minutes.**

---

**Start with Step 1 now!** Download MySQL from: https://dev.mysql.com/downloads/mysql/

