# Quick Start: SQLite → MySQL Migration

**⏱️ Total Time: 15-20 minutes**

---

## 🚀 3 Quick Commands

```bash
# 1. Create MySQL database (run as root)
mysql -u root -p < mysql_setup.sql

# 2. Apply migrations
python manage.py migrate

# 3. Load your data
python manage.py loaddata fixtures_backup.json
```

**Done!** ✅ Your system is now using MySQL.

---

## Verification (2 minutes)

```bash
# Start server
python manage.py runserver

# Visit: http://localhost:8000
# Try login - if works, MySQL is working! ✅
```

---

## Files Ready for You

| File | What to Do |
|------|-----------|
| `mysql_setup.sql` | Run this first as MySQL root |
| `fixtures_backup.json` | Auto-loaded by Django |
| `db.sqlite3.backup` | Kept for emergency rollback |
| `.env` | Updated with MySQL credentials |

---

## MySQL Credentials

```
User: eval_user
Password: eval_password
Host: localhost
Port: 3306
Database: evaluation
```

⚠️ Change password after setup for security!

---

## If Something Goes Wrong

```bash
# Rollback to SQLite (revert settings.py)
# Take < 5 minutes
```

---

**Need Details?** Read `MIGRATION_SUMMARY.md` or `MYSQL_MIGRATION_GUIDE.md`

