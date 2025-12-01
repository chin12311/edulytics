#!/bin/bash
# AWS Deployment Script - Complete Setup
# Run this on your local machine to prepare deployment files

set -e

echo "=========================================="
echo "AWS DEPLOYMENT - PHASE 1: PREP LOCAL"
echo "=========================================="

# Get current directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

echo "[1/3] Checking SSH key permissions..."
chmod 600 edulytics-key.pem
echo "✓ SSH key ready"

echo "[2/3] Creating deployment environment file..."
cat > deploy_aws.env << 'EOF'
# AWS RDS Configuration
DB_HOST=evalulytics-db.czjnyqmqjv2q.us-east-1.rds.amazonaws.com
DB_NAME=evaluation
DB_USER=eval_user
DB_PASSWORD=!eETXiuo4LHxeu6M4#sz
DB_PORT=3306

# Django Configuration
DEBUG=False
SECRET_KEY=django-insecure-y2puu=1@wfwfqr=ql86u@=5s18c#1p7d*lz9##d58e7d5dp_yf
ALLOWED_HOSTS=3.107.105.79,localhost,127.0.0.1

# Email Configuration
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=ccaedulytics@gmail.com
EMAIL_HOST_PASSWORD=vbxlxucdamjcewfn
DEFAULT_FROM_EMAIL=Edulytics System <ccaedulytics@gmail.com>
SERVER_EMAIL=ccaedulytics@gmail.com

# Other
OPENAI_API_KEY=your_openai_api_key
SCHOOL_HEAD_EMAIL=school_head@example.com
EOF
echo "✓ Environment file created: deploy_aws.env"

echo "[3/3] Summary for next steps:"
echo "=========================================="
echo "AWS Instance: 3.107.105.79"
echo "SSH Key: edulytics-key.pem"
echo ""
echo "Next Steps:"
echo "1. Open PowerShell in THIS DIRECTORY"
echo "2. Run: ./deploy_to_aws.ps1"
echo "=========================================="
