# AWS Deployment Setup Guide

## Current Situation
- **AWS IP:** 3.107.105.79
- **Local IP:** localhost:8000 (working ✅)
- **AWS Server:** Not running the Django app (that's why you get connection refused)

## Steps to Deploy to AWS

### STEP 1: SSH into AWS Instance
```bash
ssh -i edulytics-key.pem ubuntu@3.107.105.79
```

### STEP 2: Clone/Update the Code
```bash
cd /home/ubuntu
git clone https://github.com/chin12311/edulytics.git
cd edulytics
```

### STEP 3: Setup Python Environment
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### STEP 4: Setup Environment Variables
```bash
cat > .env << EOF
DEBUG=False
SECRET_KEY=your-secret-key-here
DB_HOST=your-rds-endpoint.rds.amazonaws.com
DB_NAME=evaluation
DB_USER=eval_user
DB_PASSWORD=your-password
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
OPENAI_API_KEY=your-key
EOF
```

### STEP 5: Run Migrations
```bash
python manage.py migrate
python manage.py collectstatic --noinput
```

### STEP 6: Setup Gunicorn Service
```bash
sudo nano /etc/systemd/system/gunicorn.service
```

Paste this:
```ini
[Unit]
Description=Gunicorn application server for Edulytics
After=network.target

[Service]
Type=notify
User=ubuntu
WorkingDirectory=/home/ubuntu/edulytics
ExecStart=/home/ubuntu/edulytics/venv/bin/gunicorn \
    --workers 2 \
    --bind 0.0.0.0:8000 \
    evaluationWeb.wsgi
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF
```

Then:
```bash
sudo systemctl daemon-reload
sudo systemctl start gunicorn
sudo systemctl enable gunicorn
```

### STEP 7: Setup Nginx
```bash
sudo apt-get update
sudo apt-get install -y nginx

sudo nano /etc/nginx/sites-available/default
```

Paste:
```nginx
server {
    listen 80 default_server;
    server_name _;

    client_max_body_size 20M;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /static/ {
        alias /home/ubuntu/edulytics/staticfiles/;
    }
}
```

Then:
```bash
sudo systemctl restart nginx
```

### STEP 8: Verify Everything is Running
```bash
curl http://localhost:8000/login/
sudo systemctl status gunicorn
sudo systemctl status nginx
```

### STEP 9: Access in Browser
Go to: **http://3.107.105.79/login/**

---

## Quick Troubleshooting

**App still not working?**
```bash
# Check Gunicorn status
sudo systemctl status gunicorn

# Check logs
sudo journalctl -u gunicorn -n 50

# Check Nginx status
sudo systemctl status nginx
sudo tail -f /var/log/nginx/error.log
```

**Database connection error?**
- Verify AWS RDS security group allows MySQL access
- Check .env file has correct RDS endpoint
- Test: `mysql -h your-rds-endpoint.rds.amazonaws.com -u eval_user -p evaluation`

---

## FOR NOW - Use Local Server

Until AWS is deployed, use: **http://localhost:8000/login/**

With credentials:
- Email: Christianbituonon4@gmail.com
- Password: VNxv76dBIbL@JO7UDqLo
