# 🎯 HeidiSQL Setup Guide

**Status**: Quick setup for your MySQL database  
**Database**: evaluation  
**Date**: November 9, 2025

---

## 🚀 Step-by-Step HeidiSQL Connection

### Step 1: Open HeidiSQL

1. Find **HeidiSQL** on your desktop or Start menu
2. Double-click to open it
3. You should see the main window with "Session manager" on the left

---

### Step 2: Create New Connection

**In HeidiSQL:**

1. Right-click in the left panel where it says "Unnamed"
2. Click: **"New"** → **"Session"**
3. Or look for a **"New"** button at the bottom

**You'll see a form:**

---

### Step 3: Fill in Connection Details

**Copy these exactly:**

| Field | Value |
|-------|-------|
| **Session Name** | `Evaluation DB` (or any name you like) |
| **Hostname/IP** | `localhost` |
| **User** | `eval_user` |
| **Password** | `!eETXiuo4LHxeu6M4#sz` |
| **Port** | `3306` |
| **Database** | `evaluation` |

**Screenshot of what it looks like:**
```
Session name:     [Evaluation DB        ]
Hostname/IP:      [localhost            ]
User:             [eval_user            ]
Password:         [•••••••••••••         ] ✓ Save password
Port:             [3306                 ]
Database:         [evaluation           ]
```

---

### Step 4: Test Connection

**Before saving:**

1. Look for a **"Test"** or **"Open"** button
2. Click it to verify connection works
3. You should see: **"Connected successfully"** ✅

---

### Step 5: Save Connection

1. Click **"Save"** button
2. Your connection is now saved!

---

### Step 6: Open Your Database

1. Double-click your **"Evaluation DB"** session
2. Or select it and click **"Open"**
3. **Wait for connection** (2-3 seconds)

**You should see:**

```
Left Panel (Databases):
├── evaluation
│   ├── Tables
│   │   ├── auth_user
│   │   ├── auth_group
│   │   ├── main_evaluation
│   │   ├── main_evaluationresponse
│   │   ├── main_section
│   │   └── ... (more tables)
│   └── Views
└── information_schema
```

---

## 🔍 Exploring Your Data

### View All Users

1. **Expand** the tree: `evaluation` → `Tables`
2. **Right-click** on `auth_user`
3. Click: **"Open table"** or **"Select data"**
4. You'll see all 59 users!

---

### Run a Query

**Try this:**

1. Look for **"Query"** tab or **"SQL"** button at the top
2. Or press **Ctrl + Q** to open Query Editor
3. Paste this:

```sql
SELECT username, email, is_staff, is_superuser 
FROM auth_user 
LIMIT 20;
```

4. Press **F9** or click **"Execute"** button
5. See results below! ✅

---

### View Evaluations

**Query:**
```sql
SELECT * FROM main_evaluation;
```

**You should see your 2 evaluations**

---

### View Evaluation Responses

**Query:**
```sql
SELECT 
  r.id, 
  u.username, 
  r.evaluation_id, 
  r.submitted_at
FROM main_evaluationresponse r
JOIN auth_user u ON r.evaluator_id = u.id;
```

**You should see your 4 responses**

---

## 🛠️ Useful HeidiSQL Features

### Export Data

1. Right-click a table
2. **"Export"** → Choose format (CSV, Excel, etc.)
3. Save to file

### Edit Data Directly

1. Open a table (like `auth_user`)
2. Click on any cell
3. Type to edit
4. Press **Enter** to save

### Add New Records

1. Open table
2. Scroll to bottom
3. Click **"Insert new row"** button
4. Fill in data
5. Press **Enter** to save

### Delete Records

1. Right-click a row
2. Click **"Delete"**
3. Confirm deletion

---

## 📊 Useful Queries to Try

### Users Overview

```sql
SELECT 
  username, 
  email, 
  is_staff, 
  is_superuser, 
  date_joined
FROM auth_user
ORDER BY date_joined DESC;
```

### Count Everything

```sql
SELECT 
  'Users' as item, COUNT(*) as count FROM auth_user
UNION
SELECT 'Evaluations', COUNT(*) FROM main_evaluation
UNION
SELECT 'Responses', COUNT(*) FROM main_evaluationresponse
UNION
SELECT 'Sections', COUNT(*) FROM main_section
UNION
SELECT 'User Profiles', COUNT(*) FROM main_userprofile;
```

### Recent Evaluation Responses

```sql
SELECT 
  r.id,
  u.username as evaluator,
  e.title as evaluation,
  r.submitted_at
FROM main_evaluationresponse r
JOIN auth_user u ON r.evaluator_id = u.id
JOIN main_evaluation e ON r.evaluation_id = e.id
ORDER BY r.submitted_at DESC;
```

### Find User by Email

```sql
SELECT * FROM auth_user WHERE email LIKE '%@example.com%';
```

### List All Admins

```sql
SELECT username, email, date_joined 
FROM auth_user 
WHERE is_superuser = 1;
```

---

## 🎨 Customizing HeidiSQL

### Themes

1. **Tools** → **Preferences**
2. **Appearance** → Choose your theme
3. Click **"OK"**

### Query Font Size

1. **Tools** → **Preferences**
2. **Editor** → Adjust font size
3. Click **"OK"**

### Auto-complete

1. **Tools** → **Preferences**
2. **Editor** → Enable "Code completion"
3. Click **"OK"**

---

## 🆘 Troubleshooting

### "Cannot connect to server"

**Check:**
1. MySQL is running: `Get-Service | findstr -i mysql`
2. Hostname is `localhost` (not 127.0.0.1)
3. Port is `3306`
4. Username is `eval_user`
5. Password is correct: `!eETXiuo4LHxeu6M4#sz`

### "Access denied for user"

**Try:**
1. Double-check password spelling
2. Make sure Caps Lock is OFF
3. Try pasting password from this guide
4. If still fails, reset password in MySQL:
   ```powershell
   mysql -u root -p"0Y3hCOB^HhlP%HJ!#5&u"
   ALTER USER 'eval_user'@'localhost' IDENTIFIED BY '!eETXiuo4LHxeu6M4#sz';
   FLUSH PRIVILEGES;
   EXIT;
   ```

### "Unknown database 'evaluation'"

**Verify database exists:**
```sql
SHOW DATABASES;
```

**If not there, create it:**
```sql
CREATE DATABASE evaluation CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

### "No tables showing"

**Expand the database tree:**
1. Click the **"+"** or **arrow** next to `evaluation`
2. Click **"+"** next to `Tables`
3. All 22 tables should appear

---

## ✅ Common Tasks in HeidiSQL

### Task: View all users
```
1. Expand: evaluation → Tables → auth_user
2. Right-click → "Open table"
3. See all 59 users
```

### Task: Find a specific user
```
1. Open auth_user table
2. Use Ctrl+F to search
3. Or run query:
   SELECT * FROM auth_user WHERE username = 'username';
```

### Task: Count records in a table
```
1. Right-click table
2. Click "Copy → COUNT(*)"
3. Run in Query window
```

### Task: Backup database
```
1. Right-click database name
2. Click "Export database"
3. Save as SQL file
```

### Task: See table structure
```
1. Right-click table
2. Click "Open table" or "Edit table"
3. See all columns and their types
```

---

## 🎯 Your First Session

**Try this right now:**

1. **Connect** to your database (Evaluation DB)
2. **Expand** Tables
3. **Right-click** `auth_user`
4. **Click** "Open table"
5. **Scroll** through your 59 users
6. **Click** on a username to see details

**You're now browsing your database! 🎉**

---

## 📚 Quick Reference

| Task | How |
|------|-----|
| Connect | Double-click session |
| Query | Ctrl+Q, paste SQL, F9 |
| View table | Right-click → "Open table" |
| Edit cell | Click and type |
| Search | Ctrl+F |
| Export | Right-click → "Export" |
| Refresh | F5 or Ctrl+R |
| See structure | Right-click table → "Edit table" |

---

## 🔐 Security Reminder

**Your credentials (do NOT share):**
- Host: `localhost`
- User: `eval_user`
- Password: `!eETXiuo4LHxeu6M4#sz`

HeidiSQL will remember these after first login.

---

## 🎓 Next Steps

### Now
- ✅ Connect to database
- ✅ View your data
- ✅ Run a query

### Soon
- Learn basic SQL queries
- Export data to CSV
- Understand your database structure

### Later
- Write advanced queries
- Create reports
- Set up automated backups

---

**You're all set! Start exploring your database with HeidiSQL! 🚀**

