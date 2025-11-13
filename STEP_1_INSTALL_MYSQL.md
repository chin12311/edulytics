# STEP 1: Install MySQL Server

**Current Status**: MySQL not found on system  
**What You Need to Do**: Download and install MySQL Community Server

---

## 🎯 Quick Download & Install (10 minutes)

### Step 1: Download MySQL

Click this link or copy-paste into browser:
```
https://dev.mysql.com/downloads/mysql/
```

**On that page:**
1. Select version: **MySQL 8.0** (or latest)
2. Download: **Windows (x86, 64-bit) - MSI Installer**
3. File size: ~400 MB
4. Click download

### Step 2: Install MySQL

1. Find the downloaded file (usually in Downloads folder)
2. Double-click the `.msi` file
3. Follow the installer:
   - Choose: **Developer Default** setup type
   - Keep all defaults
   - On "MySQL Server Configuration":
     - Port: `3306` (default)
     - Click Next
   - On "MySQL Router Configuration": Click Next
   - On "Advanced Options": Click Next
   - Click **Execute** when ready
   - Wait for installation to complete
   - Click **Finish**

### Step 3: Verify Installation

Open PowerShell and run:

```bash
mysql --version
```

**You should see**: `mysql Ver 8.x.x for Win64`

---

## ✅ Once You See That Version Number

You're ready! Move to: **STEP 2: Create MySQL Database**

**Then copy this command into PowerShell:**
```bash
mysql -u root -p
```

This will prompt for MySQL root password (you set this during installation).

---

**Next**: When MySQL is installed, run the command above and let me know!

