# AWS DEPLOYMENT - QUICK START

## Prerequisites Check
Before you start, verify you have:
- [ ] SSH client installed (Windows 10+ includes it)
- [ ] edulytics-key.pem file in the evaluation folder
- [ ] AWS instance 3.107.105.79 is running
- [ ] Internet connection

## AUTOMATED DEPLOYMENT (Recommended)

### Option A: Using PowerShell Script (EASIEST)

1. **Open PowerShell** in the evaluation folder
2. **Run:**
```powershell
Set-ExecutionPolicy -ExecutionPolicy Bypass -Scope Process
.\deploy_to_aws.ps1
```

Wait 5-10 minutes for deployment to complete.

3. **When done, visit:**
   - http://3.107.105.79/login/
   - Email: Christianbituonon4@gmail.com
   - Password: VNxv76dBIbL@JO7UDqLo

---

## MANUAL DEPLOYMENT (If script fails)

### Step 1: SSH into AWS
```powershell
ssh -i edulytics-key.pem ubuntu@3.107.105.79
```

### Step 2: Clone Code
```bash
cd /home/ubuntu
git clone https://github.com/chin12311/edulytics.git
cd edulytics
```

### Step 3: Setup Python
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Step 4: Create .env
```bash
cat > .env << 'EOF'
DEBUG=False
SECRET_KEY=django-insecure-y2puu=1@wfwfqr=ql86u@=5s18c#1p7d*lz9##d58e7d5dp_yf
DB_HOST=evalulytics-db.czjnyqmqjv2q.us-east-1.rds.amazonaws.com
DB_NAME=evaluation
DB_USER=eval_user
DB_PASSWORD=!eETXiuo4LHxeu6M4#sz
ALLOWED_HOSTS=3.107.105.79,localhost,127.0.0.1
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_HOST_USER=your_email@gmail.com
EMAIL_HOST_PASSWORD=your_app_password
DEFAULT_FROM_EMAIL=System Name <your_email@gmail.com>
OPENAI_API_KEY=your_openai_api_key
SCHOOL_HEAD_EMAIL=school_head@example.com
EOF
```

### Step 5: Migrations
```bash
python manage.py migrate
python manage.py collectstatic --noinput
```

### Step 6: Setup Gunicorn
```bash
sudo tee /etc/systemd/system/gunicorn.service > /dev/null << 'EOF'
[Unit]
Description=Gunicorn application server for Edulytics
After=network.target

[Service]
Type=notify
User=ubuntu
WorkingDirectory=/home/ubuntu/edulytics
Environment="PATH=/home/ubuntu/edulytics/venv/bin"
ExecStart=/home/ubuntu/edulytics/venv/bin/gunicorn \
    --workers 2 \
    --worker-class sync \
    --bind 127.0.0.1:8000 \
    --timeout 120 \
    evaluationWeb.wsgi:application
Restart=always

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable gunicorn
sudo systemctl start gunicorn
```

### Step 7: Setup Nginx
```bash
sudo apt-get update
sudo apt-get install -y nginx

sudo tee /etc/nginx/sites-available/default > /dev/null << 'EOF'
server {
    listen 80 default_server;
    server_name _;
    client_max_body_size 20M;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /static/ {
        alias /home/ubuntu/edulytics/staticfiles/;
    }
}
EOF

sudo systemctl enable nginx
sudo systemctl restart nginx
```

### Step 8: Verify
```bash
# Check services are running
sudo systemctl status gunicorn
sudo systemctl status nginx

# Test locally
curl http://127.0.0.1:8000/login/

# Exit SSH
exit
```

### Step 9: Access in Browser
- Go to: http://3.107.105.79/login/
- Login with admin credentials

---

## TROUBLESHOOTING

### App not accessible?
```bash
# SSH in and check
ssh -i edulytics-key.pem ubuntu@3.107.105.79

# Check Gunicorn
sudo systemctl status gunicorn
sudo journalctl -u gunicorn -n 50

# Check Nginx
sudo systemctl status nginx
sudo tail -f /var/log/nginx/error.log

# Check ports
netstat -tlnp
```

### Database connection error?
```bash
# SSH in and test
mysql -h evalulytics-db.czjnyqmqjv2q.us-east-1.rds.amazonaws.com -u eval_user -p evaluation -e "SELECT COUNT(*) FROM auth_user;"

# Check .env file
cat .env
```

### Python errors?
```bash
# SSH in and check logs
sudo journalctl -u gunicorn -n 100 | grep ERROR

# Try running directly
cd /home/ubuntu/edulytics
source venv/bin/activate
python manage.py runserver 0.0.0.0:8000
```

---

## QUICK COMMANDS

### Restart application after code changes:
```bash
ssh -i edulytics-key.pem ubuntu@3.107.105.79
sudo systemctl restart gunicorn
```

### View live logs:
```bash
ssh -i edulytics-key.pem ubuntu@3.107.105.79
sudo journalctl -u gunicorn -f
```

### SSH for maintenance:
```bash
ssh -i edulytics-key.pem ubuntu@3.107.105.79
cd /home/ubuntu/edulytics
source venv/bin/activate
# Now you can run any Django commands
python manage.py shell
```

---

**Questions?** Check the AWS_DEPLOYMENT_GUIDE.md for more details!
