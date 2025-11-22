AWS EC2 INSTANCE TROUBLESHOOTING
================================

ISSUE: SSH connection timeout to 3.107.105.79
  Error: "Connection timed out"
  Meaning: Instance is not responding on port 22

QUICK FIXES TO TRY:

1. CHECK AWS CONSOLE (FIRST):
   - Go to: https://console.aws.amazon.com/ec2/
   - Look for instance "3.107.105.79" or named "edulytics"
   - Check "Instance State":
     ✓ "running" = Go to step 2
     ✗ "stopped" = Click it, then "Instance State" → "Start"
     ✗ "terminated" = Need to create new instance

2. IF INSTANCE IS RUNNING:
   - Check "Security Groups" tab
   - Verify it allows inbound SSH (port 22) from your IP
   - If not, edit the security group to allow SSH

3. IF INSTANCE DETAILS ARE DIFFERENT:
   - The IP might have changed (AWS reassigns IPs when stopped)
   - Get the new IP from AWS Console and use that

4. ALTERNATIVE - Use AWS Systems Manager Session Manager:
   - Requires instance to have IAM role with EC2-SSM permissions
   - More secure, doesn't need SSH key
   - Can connect directly from AWS Console

WHAT TO DO NOW:

Option A: START THE INSTANCE (FASTEST)
  1. Go to AWS Console
  2. Find your instance
  3. Right-click → "Instance State" → "Start"
  4. Wait 2-3 minutes
  5. Tell me the new IP or confirm it's the same

Option B: USE INSTANCE CONNECT (if available)
  1. Go to AWS Console
  2. Select instance
  3. Click "Connect" button
  4. Choose "EC2 Instance Connect"
  5. This opens a browser terminal

Option C: CHECK SECURITY GROUPS
  1. Go to Security Groups in AWS Console
  2. Find the one attached to your instance
  3. Edit inbound rules
  4. Add rule: SSH (port 22), Source: Your IP or 0.0.0.0/0

================================================

AFTER INSTANCE IS RUNNING:

Once you confirm the instance is up, run this command:

  ssh -i "c:\Users\ADMIN\eval\evaluation\edulytics-key.pem" ubuntu@3.107.105.79 "cd /home/ubuntu/edulytics && source venv/bin/activate && python manage.py runserver 0.0.0.0:8000"

Then access: http://3.107.105.79:8000/login/

================================================

LET ME KNOW:
1. Is the instance running in AWS Console?
2. What is the current instance state?
3. If you need to start it, let me know when it's ready
