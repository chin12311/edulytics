#!/bin/bash

echo "====== AWS Deployment Fix ======"
echo ""

# Step 0: Remove SQLite to force MySQL connection
echo "Step 0: Removing SQLite database..."
rm -f db.sqlite3
echo "Done"

# Step 1: Remove conflicting files
echo "Step 1: Removing conflicting static files..."
rm -f staticfiles/img/phoenix-backgrounddd.png
echo "Done"

# Step 1.5: Activate venv and install requirements
echo ""
echo "Step 1.5: Activating virtual environment and installing dependencies..."
source venv/bin/activate
pip install -r requirements.txt --quiet
echo "Dependencies installed"

# Step 2: Pull latest code
echo ""
echo "Step 2: Pulling latest code from GitHub..."
git pull origin main
if [ $? -eq 0 ]; then
    echo "Git pull successful"
else
    echo "Git pull failed"
    exit 1
fi

# Step 3: Run migrations
echo ""
echo "Step 3: Running database migrations..."
python manage.py migrate
echo "Migrations complete"

# Step 4: Collect static files
echo ""
echo "Step 4: Collecting static files..."
python manage.py collectstatic --noinput
echo "Static files collected"

# Step 5: Restart web server
echo ""
echo "Step 5: Restarting web server..."
sudo systemctl restart gunicorn
if [ $? -eq 0 ]; then
    echo "Gunicorn restarted successfully"
else
    echo "Note: Could not restart Gunicorn. You may need to restart manually"
fi

# Step 6: Verify
echo ""
echo "Step 6: Verifying deployment..."
git log --oneline -1

echo ""
echo "====== Deployment Complete! ======"
echo ""
echo "Your system is now running the latest version with:"
echo "  - Fixed delete account function"
echo "  - Database cleanup scripts"
echo "  - Updated templates"
echo "  - All latest features"
