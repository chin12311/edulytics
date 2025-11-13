# 🔐 Account Security Guide - SQLite to MySQL Migration

**Date**: November 9, 2025  
**Status**: Critical - Review Before Going Live  
**Priority**: HIGH ⚠️

---

## 🚨 Current Security Status

### ⚠️ PASSWORDS EXPOSED IN CONFIGURATION

Your system currently has **default passwords** in plain text. These need to be changed immediately before using in production.

| Component | Current Setting | Risk Level | Status |
|-----------|-----------------|-----------|--------|
| MySQL Root | `Christian_ian12345` | 🔴 CRITICAL | Needs change |
| MySQL eval_user | `eval_password` | 🔴 CRITICAL | Needs change |
| Django SECRET_KEY | Default | 🟡 HIGH | Needs change |
| DEBUG Mode | (Check settings) | 🟡 HIGH | Should be False |

---

## 🛠️ Immediate Action Items

### 1. Change MySQL Root Password ⚠️

**Current Status**: Using `Christian_ian12345`  
**Action Required**: Change to strong password

**Step 1: Change the password**
```powershell
mysql -u root -p"Christian_ian12345"
```

**Step 2: When MySQL prompt appears, run:**
```sql
ALTER USER 'root'@'localhost' IDENTIFIED BY 'YourNewStrongPassword123!';
FLUSH PRIVILEGES;
EXIT;
```

**Step 3: Save it in a secure location:**
- Use a password manager (LastPass, 1Password, etc.)
- DO NOT store in plain text files
- DO NOT commit to Git

---

### 2. Change MySQL eval_user Password ⚠️

**Current Status**: Using `eval_password`  
**Action Required**: Change to strong password

**Step 1: Login as root with new password**
```powershell
mysql -u root -p
```

**Step 2: When prompt appears:**
```sql
ALTER USER 'eval_user'@'localhost' IDENTIFIED BY 'YourNewEvalPassword123!';
FLUSH PRIVILEGES;
EXIT;
```

**Step 3: Update your .env file**
```
DB_PASSWORD=YourNewEvalPassword123!
```

**Step 4: Restart Django**
```powershell
Ctrl+C (to stop server)
python manage.py runserver
```

---

### 3. Generate New Django SECRET_KEY 🔑

**Why**: Django uses this to sign sessions and tokens. Default is security risk.

**Step 1: Generate a new secure key**
```powershell
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

**Step 2: Copy the output (looks like): `django-insecure-a#b$c%d^e&f*g(h)i_j+k=l...`**

**Step 3: Update your .env or settings.py**

Find this line in `settings.py`:
```python
SECRET_KEY = 'django-insecure-...'
```

Replace with your new key:
```python
SECRET_KEY = os.getenv('SECRET_KEY', 'your-new-key-here')
```

Or add to `.env`:
```
SECRET_KEY=your-new-generated-key
```

---

### 4. Disable DEBUG Mode 🐛

**Current Status**: Check `settings.py` line ~20  
**Action Required**: Set to False for production

**Find this line:**
```python
DEBUG = True
```

**Change to:**
```python
DEBUG = False
```

Or use environment variable:
```python
DEBUG = os.getenv('DEBUG', 'False') == 'True'
```

---

## 🔒 Password Security Best Practices

### Strong Password Requirements

Your passwords should have:
- ✅ Minimum 16 characters
- ✅ Mix of UPPERCASE and lowercase
- ✅ At least one number (0-9)
- ✅ At least one special character (!@#$%^&*)
- ✅ No dictionary words
- ✅ No personal information

### Example Strong Passwords

```
✅ GOOD:     P@ssw0rdMigr8tion2025!Secure
✅ GOOD:     MySQL_Ev@l_2025_Secure!Pass
❌ BAD:      password123
❌ BAD:      eval_password
❌ BAD:      admin123456
```

### Generate Secure Passwords

```powershell
# Using Python
python -c "import secrets; import string; chars = string.ascii_letters + string.digits + '!@#$%^&*'; print(''.join(secrets.choice(chars) for _ in range(20)))"
```

---

## 📋 .env File Security

### Current .env Content

Your `.env` file currently has:
```
DB_NAME=evaluation
DB_USER=eval_user
DB_PASSWORD=eval_password
DB_HOST=localhost
DB_PORT=3306
```

### 🔴 Issues

1. Passwords in plain text
2. Not git-ignored
3. Visible to anyone with file access

### ✅ Fix It

**Step 1: Secure the .env file**
```powershell
# Restrict file permissions (Windows)
icacls ".env" /inheritance:r /grant:r "%USERNAME%:F"
```

**Step 2: Ensure .env is in .gitignore**
```
cat .gitignore
```

Look for: `.env` (if not there, add it)

**Step 3: Update .env with new passwords**
```
DB_NAME=evaluation
DB_USER=eval_user
DB_PASSWORD=YourNewStrongPassword123!
DB_HOST=localhost
DB_PORT=3306
SECRET_KEY=your-new-secret-key-here
DEBUG=False
```

---

## 🔐 Django User Accounts

### Check Your Django Users

```powershell
python manage.py shell -c "
from django.contrib.auth.models import User
for user in User.objects.all()[:10]:
    print(f'{user.username}: is_staff={user.is_staff}, is_superuser={user.is_superuser}')
"
```

### Secure Your Admin Account

**Find admin user:**
```powershell
python manage.py shell -c "from django.contrib.auth.models import User; admin = User.objects.get(is_superuser=True); print(f'Admin: {admin.username}')"
```

**Change admin password:**
```powershell
python manage.py changepassword admin
```

Or in Django shell:
```powershell
python manage.py shell
```

Then:
```python
from django.contrib.auth.models import User
user = User.objects.get(username='admin')
user.set_password('NewAdminPassword123!')
user.save()
print('Password changed!')
```

---

## 🔓 Access Control

### Current Security Model

**Who has access?**
- ✅ `eval_user`: Can access evaluation database
- ✅ `root`: Full MySQL access
- ⚠️ All 59 users: Django login access

### Restrict Database Access

**MySQL only allows localhost:**
```sql
SHOW GRANTS FOR 'eval_user'@'localhost';
```

**If you see '%', restrict it:**
```sql
ALTER USER 'eval_user'@'%' IDENTIFIED BY 'password';
DROP USER 'eval_user'@'%';
CREATE USER 'eval_user'@'localhost' IDENTIFIED BY 'password';
GRANT ALL PRIVILEGES ON evaluation.* TO 'eval_user'@'localhost';
```

---

## 🛡️ Production Security Checklist

### Before Going Live

- [ ] MySQL root password changed
- [ ] MySQL eval_user password changed
- [ ] Django SECRET_KEY regenerated
- [ ] DEBUG mode set to False
- [ ] ALLOWED_HOSTS configured
- [ ] .env file secured and git-ignored
- [ ] Admin account password changed
- [ ] SSL/HTTPS enabled (if accessible from internet)
- [ ] Database backups enabled
- [ ] Database password policy set
- [ ] Regular password rotation planned
- [ ] Audit logging enabled

### Django Settings to Check

```python
# settings.py

# 1. DEBUG
DEBUG = False  # ✅ Should be False

# 2. ALLOWED_HOSTS
ALLOWED_HOSTS = ['localhost', '127.0.0.1']  # ✅ Add your domain

# 3. SECRET_KEY
SECRET_KEY = 'your-random-secret-key'  # ✅ Generated and unique

# 4. Database
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': os.getenv('DB_NAME'),
        'USER': os.getenv('DB_USER'),
        'PASSWORD': os.getenv('DB_PASSWORD'),
        'HOST': os.getenv('DB_HOST', 'localhost'),
        'PORT': os.getenv('DB_PORT', '3306'),
    }
}
```

---

## 🔄 Password Rotation Plan

### Recommended Schedule

- **Initial Change**: NOW (before using system)
- **MySQL Passwords**: Change every 90 days
- **Django SECRET_KEY**: Change every 180 days
- **Admin Password**: Change every 60 days
- **eval_user**: Change every 90 days

### How to Rotate Passwords

**For MySQL:**
```sql
ALTER USER 'eval_user'@'localhost' IDENTIFIED BY 'NewPassword123!';
FLUSH PRIVILEGES;
```

**For Django Admin:**
```powershell
python manage.py changepassword admin
```

**For Django SECRET_KEY:**
1. Generate new key: `python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"`
2. Update .env
3. Restart Django

---

## 🚨 Security Monitoring

### Enable MySQL Logging

```sql
SHOW VARIABLES LIKE 'log%';
SET GLOBAL general_log = 'ON';
SET GLOBAL log_output = 'FILE';
```

### Monitor Django Logs

```powershell
# Create logs directory
mkdir logs

# Run with logging
python manage.py runserver --log-level DEBUG 2>&1 | tee logs/django.log
```

---

## 🔑 Password Storage

### ❌ DO NOT

- Store passwords in code
- Store passwords in Git
- Use same password everywhere
- Write passwords in comments
- Share passwords via email
- Use weak passwords

### ✅ DO

- Use a password manager
- Store in .env (git-ignored)
- Use strong, unique passwords
- Rotate passwords regularly
- Use environment variables
- Enable 2FA where possible

---

## 🚨 If You Suspect a Security Breach

1. **Immediately change all passwords**
   ```powershell
   mysql -u root -p
   ALTER USER 'eval_user'@'localhost' IDENTIFIED BY 'new_emergency_password';
   ```

2. **Check MySQL audit log**
   ```sql
   SELECT * FROM mysql.general_log LIMIT 100;
   ```

3. **Review Django access logs**
   ```powershell
   cat logs/django.log
   ```

4. **Disable suspicious accounts**
   ```sql
   UPDATE auth_user SET is_active=0 WHERE id=5;
   ```

5. **Backup database immediately**
   ```powershell
   mysqldump -u eval_user -p evaluation > emergency_backup.sql
   ```

---

## 📞 Security Summary

| Item | Current | Required | Action |
|------|---------|----------|--------|
| MySQL Root Pass | christian_ian12345 | Strong | Change NOW |
| eval_user Pass | eval_password | Strong | Change NOW |
| Django SECRET_KEY | Default | Unique | Generate NOW |
| DEBUG Mode | (Check) | False | Update NOW |
| .env Protected | No | Yes | Secure NOW |
| Admin Pass | Unknown | Strong | Change NOW |

---

## ✅ Next Steps

### Immediately (Do This Now!)

1. **Change MySQL root password** - 2 minutes
2. **Change eval_user password** - 2 minutes  
3. **Generate new Django SECRET_KEY** - 1 minute
4. **Update .env file** - 1 minute
5. **Set DEBUG = False** - 1 minute
6. **Change admin password** - 1 minute

**Total Time: ~8 minutes**

### Before Production

7. Secure .env file permissions
8. Enable database logging
9. Set up automated backups
10. Plan password rotation schedule

---

## 🎓 Security Resources

### Django Security
- https://docs.djangoproject.com/en/stable/topics/security/
- https://docs.djangoproject.com/en/stable/ref/settings/#secret-key

### MySQL Security
- https://dev.mysql.com/doc/refman/8.0/en/security.html
- https://dev.mysql.com/doc/refman/8.0/en/user-names.html

### General Security
- Use a password manager (1Password, Bitwarden, KeePass)
- Enable 2FA where available
- Keep software updated
- Regular security audits

---

## ⚠️ Important Reminder

**Your current system uses default passwords. This is a security risk.**

Even though it's running locally, good security practices now will:
- ✅ Protect user data
- ✅ Prevent unauthorized access
- ✅ Meet compliance requirements
- ✅ Build user trust
- ✅ Prepare for scaling

---

**Please complete the security changes before continuing to use the system in any serious capacity!**

🔒 Your system security depends on it. 🔒

