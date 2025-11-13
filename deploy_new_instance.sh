#!/bin/bash
# Deploy script for new AWS instance
# Run this on your NEW EC2 instance after launching it

set -e

echo "🚀 Starting Edulytics Deployment..."

# Update system packages
echo "📦 Updating system packages..."
sudo apt-get update
sudo apt-get upgrade -y

# Install required packages
echo "📥 Installing dependencies..."
sudo apt-get install -y \
    python3-pip \
    python3-venv \
    python3-dev \
    mysql-client \
    git \
    nginx \
    supervisor

# Clone the repository
echo "📚 Cloning repository..."
cd /home/ubuntu
if [ ! -d "edulytics" ]; then
    git clone https://github.com/chin12311/edulytics.git
    cd edulytics
else
    cd edulytics
    git pull origin main
fi

# Create virtual environment
echo "🐍 Setting up Python virtual environment..."
python3 -m venv venv
source venv/bin/activate

# Install Python dependencies
echo "📦 Installing Python packages..."
pip install --upgrade pip setuptools wheel
pip install -r requirements.txt

# Create .env file
echo "⚙️  Creating .env file..."
cat > .env << 'EOF'
# Database Configuration
DB_NAME=evaluation
DB_USER=eval_user
DB_PASSWORD=!eETXiuo4LHxeu6M4#sz
DB_HOST=54.66.185.78
DB_PORT=3306
DEBUG=False

# Email Configuration
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_HOST_USER=ccaedulytics@gmail.com
EMAIL_HOST_PASSWORD=vbxlxucdamjcewfn
DEFAULT_FROM_EMAIL=Edulytics System <ccaedulytics@gmail.com>
SERVER_EMAIL=ccaedulytics@gmail.com

# Security
SECRET_KEY=$@*&^ff#vxu_)5at$!qy%+_=-&@@09rfu6&^gs_vo&0am01&w$
OPENAI_API_KEY=sk-proj-OYXSc33qhKKPbtiJIPgEv29SuBKALPopag8Lctbdcx5tmADXliXkHmg-PODIUrEWjptdfDGocbT3BlbkBroku

# Edulytics Settings
SCHOOL_HEAD_EMAIL=cibituonon@cca.edu.ph
EOF

# Collect static files
echo "🎨 Collecting static files..."
python manage.py collectstatic --noinput --clear

# Run migrations
echo "🗄️  Running database migrations..."
python manage.py migrate --run-syncdb

# Create missing profiles
echo "👥 Creating missing user profiles..."
python manage.py shell << 'PYEOF'
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'evaluationWeb.settings')
import django
django.setup()

from django.contrib.auth.models import User
from main.models import UserProfile, Role

created_count = 0
for user in User.objects.all():
    if not hasattr(user, 'userprofile'):
        role = Role.ADMIN if user.username.lower() == 'admin' else Role.STUDENT
        profile = UserProfile(
            user=user,
            display_name=user.first_name or user.username,
            role=role,
        )
        profile.save(skip_validation=True)
        created_count += 1

print(f"✅ Created {created_count} UserProfile records")
PYEOF

# Configure Gunicorn
echo "⚙️  Setting up Gunicorn..."
sudo bash -c 'cat > /etc/systemd/system/gunicorn.service << EOF
[Unit]
Description=Gunicorn daemon for evaluationWeb
After=network.target
Wants=mysqld.service

[Service]
Type=notify
User=ubuntu
Group=www-data
WorkingDirectory=/home/ubuntu/edulytics
Environment="PATH=/home/ubuntu/edulytics/venv/bin"
ExecStart=/home/ubuntu/edulytics/venv/bin/gunicorn \
    --workers 2 \
    --worker-class sync \
    --worker-connections 100 \
    --bind 0.0.0.0:8000 \
    --timeout 60 \
    --access-logfile - \
    evaluationWeb.wsgi

Restart=always
RestartSec=10s

[Install]
WantedBy=multi-user.target
EOF'

# Configure Nginx
echo "🔌 Configuring Nginx..."
sudo bash -c 'cat > /etc/nginx/sites-available/default << EOF
upstream gunicorn {
    server 127.0.0.1:8000;
}

server {
    listen 80 default_server;
    listen [::]:80 default_server;
    
    client_max_body_size 100M;

    location /static/ {
        alias /home/ubuntu/edulytics/staticfiles/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    location /images/ {
        alias /home/ubuntu/edulytics/media/;
        expires 7d;
    }

    location / {
        proxy_pass http://gunicorn;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_read_timeout 60s;
    }
}
EOF'

# Start services
echo "🚀 Starting services..."
sudo systemctl daemon-reload
sudo systemctl enable gunicorn
sudo systemctl start gunicorn
sudo systemctl enable nginx
sudo systemctl restart nginx

# Verify services
echo ""
echo "✅ DEPLOYMENT COMPLETE!"
echo ""
echo "Gunicorn status:"
sudo systemctl status gunicorn --no-pager | head -5
echo ""
echo "Nginx status:"
sudo systemctl status nginx --no-pager | head -5
echo ""
echo "🎉 Application is ready!"
echo "Visit: http://$(hostname -I | awk '{print $1}'):80"
