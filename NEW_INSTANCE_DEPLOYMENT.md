# 🚀 New AWS Instance Deployment - Step by Step

## **Phase 1: AWS Console (5 minutes)**

### Step 1: Terminate Old Instance
1. Open: https://console.aws.amazon.com
2. Go to **EC2 → Instances** (left menu)
3. Find instance with IP `54.66.185.78`
4. **Right-click** → **Instance State** → **Terminate**
5. Click **"Terminate"** to confirm
6. ⏳ Wait for it to terminate (status changes to "terminated")

### Step 2: Launch New Instance
1. Click **"Launch Instances"** (orange button, top right)
2. Fill in settings:

| Field | Value |
|-------|-------|
| Name | `edulytics-production` |
| AMI | `Ubuntu Server 22.04 LTS` |
| Instance Type | `t2.micro` |
| Key Pair | `edulytics-key` |
| Security Group | `launch-wizard-1` or existing |
| Storage | `30 GB` (gp2) |

3. Click **"Launch Instance"**
4. ⏳ Wait 2-3 minutes for instance to start

### Step 3: Get New IP Address
1. Go to **EC2 → Instances**
2. Find your new instance
3. **Copy the Public IPv4 address** (e.g., `3.xx.xxx.xxx`)
4. **SAVE THIS IP** - you'll need it

---

## **Phase 2: SSH & Deploy (10 minutes)**

### Step 4: SSH Into New Instance

Open PowerShell and run:

```powershell
$NewIP = "YOUR_NEW_IP_HERE"  # Replace with actual IP from Step 3
ssh -i "C:\Users\ADMIN\eval\evaluation\edulytics-key.pem" ubuntu@$NewIP
```

When it asks: `Are you sure you want to continue connecting (yes/no)?`
- Type: `yes` and press Enter

### Step 5: Deploy Application

Once SSH'd in, run this command (copy the whole thing):

```bash
sudo apt-get update && \
sudo apt-get install -y curl && \
curl -sSL https://raw.githubusercontent.com/chin12311/edulytics/main/deploy_new_instance.sh | bash
```

⏳ This will take **5-10 minutes**. Watch for the green checkmarks ✅

### Step 6: Verify Deployment

After deployment finishes, run:

```bash
curl http://localhost:8000
```

You should see HTML output (the website loading).

---

## **Phase 3: Test Website (2 minutes)**

### Step 7: Test in Browser

Open your web browser and go to:
```
http://YOUR_NEW_IP_HERE
```

You should see the Edulytics login page! 🎉

Try logging in with:
- **Username:** `Admin`
- **Password:** (use your admin password)

---

## **Phase 4: Apply Optimizations (Optional - 5 minutes)**

If you want to apply the performance optimizations we created:

```bash
bash /home/ubuntu/edulytics/optimize_aws.sh
```

---

## **Common Issues & Fixes**

### Issue 1: "Permission denied" when SSH'ing
**Fix:** Check that your key permissions are correct:
```powershell
$KeyPath = "C:\Users\ADMIN\eval\evaluation\edulytics-key.pem"
icacls $KeyPath /inheritance:r /grant:r "${env:username}:F"
```

### Issue 2: Website shows "502 Bad Gateway" 
**Fix:** Wait 5 minutes for services to fully start, then refresh browser

### Issue 3: "Connection timed out" error
**Fix:** 
1. Check Security Group allows HTTP (port 80)
2. Verify instance is in "running" state
3. Check instance has Public IP assigned

### Issue 4: Can't log in - "Account not found"
**Fix:** The users_only.json fixture might not have been imported yet. SSH in and run:
```bash
cd /home/ubuntu/edulytics
source venv/bin/activate
python manage.py loaddata users_only.json
```

---

## **Summary**

| Step | Time | Action |
|------|------|--------|
| 1-3 | ~5 min | Terminate old + launch new instance in AWS Console |
| 4-5 | ~10 min | SSH and deploy with one command |
| 6-7 | ~2 min | Test website works |
| **Total** | **~17 minutes** | ✅ Live production system! |

---

## **Once Live - Important Notes**

✅ **Record your new IP address:** `_______________`

✅ **Update DNS if you have a domain name** (point to new IP)

✅ **Application should now be:**
- 2-4x faster (with optimizations)
- Using 2 Gunicorn workers (better RAM usage)
- Serving static files via Nginx (faster)
- MySQL query caching enabled

---

**Next: Follow the steps above!** 🚀
