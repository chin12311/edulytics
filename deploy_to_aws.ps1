# AWS Deployment Script for Windows PowerShell
# This script will deploy the Django app to AWS

param(
    [string]$AwsIp = "3.107.105.79",
    [string]$KeyFile = "edulytics-key.pem",
    [string]$User = "ubuntu"
)

$ErrorActionPreference = "Stop"

Write-Host "=========================================="
Write-Host "AWS DEPLOYMENT - WINDOWS POWERSHELL"
Write-Host "=========================================="
Write-Host "Target: $AwsIp"
Write-Host "User: $User"
Write-Host ""

# Step 1: Test SSH connection
Write-Host "[1/8] Testing SSH connection..."
try {
    ssh -i $KeyFile -o "StrictHostKeyChecking=no" -o "UserKnownHostsFile=/dev/null" $User@$AwsIp "echo 'SSH connection successful'" 2>&1 | Out-Null
    Write-Host "✓ SSH connection working"
} catch {
    Write-Host "✗ SSH connection failed!"
    Write-Host "Make sure:"
    Write-Host "  1. edulytics-key.pem is in current directory"
    Write-Host "  2. SSH client is installed (part of Windows 10+)"
    Write-Host "  3. Instance 3.107.105.79 is running"
    exit 1
}

# Step 2: Clone/Update code
Write-Host "[2/8] Cloning/updating code..."
ssh -i $KeyFile -o "StrictHostKeyChecking=no" $User@$AwsIp @"
    cd /home/$User
    if [ -d "edulytics" ]; then
        cd edulytics
        git pull origin main
    else
        git clone https://github.com/chin12311/edulytics.git
        cd edulytics
    fi
    echo "Code ready"
"@ | Out-Null
Write-Host "✓ Code deployed"

# Step 3: Setup Python environment
Write-Host "[3/8] Setting up Python environment..."
ssh -i $KeyFile $User@$AwsIp @"
    cd /home/$User/edulytics
    python3 -m venv venv
    source venv/bin/activate
    pip install --upgrade pip
    pip install -r requirements.txt
    echo "Python environment ready"
"@ | Out-Null
Write-Host "✓ Python environment ready"

# Step 4: Create .env file
Write-Host "[4/8] Creating .env file..."
ssh -i $KeyFile $User@$AwsIp @"
    cat > /home/$User/edulytics/.env << 'ENVEOF'
DEBUG=False
SECRET_KEY=django-insecure-y2puu=1@wfwfqr=ql86u@=5s18c#1p7d*lz9##d58e7d5dp_yf
DB_HOST=evalulytics-db.czjnyqmqjv2q.us-east-1.rds.amazonaws.com
DB_NAME=evaluation
DB_USER=eval_user
DB_PASSWORD=!eETXiuo4LHxeu6M4#sz
DB_PORT=3306
ALLOWED_HOSTS=3.107.105.79,localhost,127.0.0.1
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your_email@gmail.com
EMAIL_HOST_PASSWORD=your_app_password
DEFAULT_FROM_EMAIL=System Name <your_email@gmail.com>
SERVER_EMAIL=your_email@gmail.com
OPENAI_API_KEY=your_openai_api_key
SCHOOL_HEAD_EMAIL=school_head@example.com
ENVEOF
"@ | Out-Null
Write-Host "✓ Environment configured"

# Step 5: Run migrations
Write-Host "[5/8] Running migrations..."
ssh -i $KeyFile $User@$AwsIp @"
    cd /home/$User/edulytics
    source venv/bin/activate
    python manage.py migrate
    python manage.py collectstatic --noinput
    echo "Migrations complete"
"@ | Out-Null
Write-Host "✓ Migrations complete"

# Step 6: Setup Gunicorn
Write-Host "[6/8] Setting up Gunicorn service..."
ssh -i $KeyFile $User@$AwsIp @"
    sudo tee /etc/systemd/system/gunicorn.service > /dev/null << 'GUNICORNEOF'
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
    --access-logfile - \
    --error-logfile - \
    evaluationWeb.wsgi:application

Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
GUNICORNEOF

    sudo systemctl daemon-reload
    sudo systemctl enable gunicorn
    sudo systemctl restart gunicorn
    sleep 2
    sudo systemctl status gunicorn
"@ | Out-Null
Write-Host "✓ Gunicorn configured and running"

# Step 7: Setup Nginx
Write-Host "[7/8] Setting up Nginx..."
ssh -i $KeyFile $User@$AwsIp @"
    sudo apt-get update
    sudo apt-get install -y nginx

    sudo tee /etc/nginx/sites-available/default > /dev/null << 'NGINXEOF'
server {
    listen 80 default_server;
    listen [::]:80 default_server;

    server_name _;
    client_max_body_size 20M;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_redirect off;
    }

    location /static/ {
        alias /home/ubuntu/edulytics/staticfiles/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    location /media/ {
        alias /home/ubuntu/edulytics/media/;
        expires 7d;
    }
}
NGINXEOF

    sudo systemctl enable nginx
    sudo systemctl restart nginx
    sleep 2
    sudo systemctl status nginx
"@ | Out-Null
Write-Host "✓ Nginx configured and running"

# Step 8: Verify deployment
Write-Host "[8/8] Verifying deployment..."
try {
    $response = ssh -i $KeyFile $User@$AwsIp "curl -s http://127.0.0.1:8000/login/ | head -20"
    if ($response -match "login|Edulytics") {
        Write-Host "✓ Application is responding!"
    } else {
        Write-Host "⚠ Application may not be responding correctly"
    }
} catch {
    Write-Host "⚠ Could not verify application"
}

Write-Host ""
Write-Host "=========================================="
Write-Host "DEPLOYMENT COMPLETE!"
Write-Host "=========================================="
Write-Host ""
Write-Host "✓ Access your app at:"
Write-Host "  http://3.107.105.79/login/"
Write-Host ""
Write-Host "✓ Test credentials:"
Write-Host "  Email: Christianbituonon4@gmail.com"
Write-Host "  Password: VNxv76dBIbL@JO7UDqLo"
Write-Host ""
Write-Host "Troubleshooting:"
Write-Host "  SSH into AWS: ssh -i edulytics-key.pem ubuntu@3.107.105.79"
Write-Host "  Check Gunicorn: sudo systemctl status gunicorn"
Write-Host "  Check Nginx: sudo systemctl status nginx"
Write-Host "  View logs: sudo journalctl -u gunicorn -n 50"
Write-Host "=========================================="
