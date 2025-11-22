# DEPLOY TO AWS - USING BROWSER TERMINAL

Since SSH is having connection issues, we'll use **EC2 Instance Connect** - a browser-based terminal.

## STEP 1: Open Browser Terminal

1. Go to AWS Console: https://console.aws.amazon.com/ec2/
2. Find your instance (3.107.105.79)
3. Click it to select
4. Click orange **"Connect"** button at top right
5. Click **"EC2 Instance Connect"** tab (NOT "SSH client")
6. Click **"Connect"** button
7. **A browser terminal will open in a new window**

---

## STEP 2: Run Commands in Browser Terminal

Copy and paste **each command** one at a time into the browser terminal. Press Enter after each.

### Command 1: Activate Virtual Environment & Check Status
```
cd /home/ubuntu/edulytics && source venv/bin/activate && python manage.py check
```
Expected output: "System check identified no issues (0 silenced)."

---

### Command 2: Start Gunicorn Service
```
sudo systemctl start gunicorn
```
No output = success. Gunicorn is now running.

---

### Command 3: Start Nginx Service
```
sudo systemctl enable nginx && sudo systemctl restart nginx
```
No output = success. Nginx is now running.

---

### Command 4: Verify Services Are Running
```
sudo systemctl status gunicorn && sudo systemctl status nginx
```
Look for "Active: active (running)"

---

## STEP 3: Test in Browser

Once both services are running, **open a new browser tab:**

```
http://3.107.105.79/login/
```

---

## STEP 4: Login with Test Account

**Email:** Christianbituonon4@gmail.com
**Password:** VNxv76dBIbL@JO7UDqLo

You should see the login page and be able to log in!

---

## TROUBLESHOOTING

### If Gunicorn won't start:
```
sudo systemctl restart gunicorn
sudo journalctl -u gunicorn -n 50
```

### If Nginx won't start:
```
sudo nginx -t
sudo systemctl restart nginx
sudo journalctl -u nginx -n 50
```

### Check what's running on port 80:
```
sudo netstat -tuln | grep :80
```

### Check what's running on port 8000:
```
sudo netstat -tuln | grep :8000
```

---

## Let me know once you see the login page at http://3.107.105.79/login/!
