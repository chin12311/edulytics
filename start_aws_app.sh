#!/bin/bash
# AWS Deployment - Get Application Running

echo "=========================================="
echo "AWS DEPLOYMENT - START APPLICATION"
echo "=========================================="

# Change to app directory
cd /home/ubuntu/edulytics

# Activate virtual environment
source venv/bin/activate

# Install/update dependencies
pip install -r requirements.txt

# Run migrations
python manage.py migrate

# Collect static files
python manage.py collectstatic --noinput

# Start Gunicorn
gunicorn --workers 2 \
         --worker-class sync \
         --bind 0.0.0.0:8000 \
         --timeout 120 \
         evaluationWeb.wsgi

echo "=========================================="
echo "Application started on port 8000"
echo "=========================================="
