#!/bin/bash
# AWS Deployment Script - Fix git conflicts and update

echo "Step 1: Stashing local changes..."
git stash

echo "Step 2: Pulling latest code from GitHub..."
git pull origin main

echo "Step 3: Running migrations..."
python manage.py migrate

echo "Step 4: Collecting static files..."
python manage.py collectstatic --noinput

echo "Step 5: Restarting Django application..."
# Determine which process manager is running
if pgrep -f "gunicorn" > /dev/null; then
    echo "Restarting Gunicorn..."
    sudo systemctl restart gunicorn
elif pgrep -f "uwsgi" > /dev/null; then
    echo "Restarting uWSGI..."
    sudo systemctl restart uwsgi
elif pgrep -f "supervisor" > /dev/null; then
    echo "Restarting Supervisor..."
    sudo supervisorctl restart all
else
    echo "No process manager found. Please restart Django manually."
fi

echo "Deployment complete!"
git log --oneline -1
