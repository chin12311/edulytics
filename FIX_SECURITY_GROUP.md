# FIX AWS SECURITY GROUP - SSH ACCESS

Your EC2 instance is running but **SSH port 22 is blocked** by the security group.

## QUICK FIX (2 minutes):

1. **Go to AWS Console**
   - Open: https://console.aws.amazon.com/ec2/

2. **Find your instance**
   - Look for 3.107.105.79 in Instances list
   - Click it to select it

3. **Click "Security" tab** (in instance details)

4. **Click the Security Group name** (it's a link, like "sg-xxxxx")

5. **Click "Edit inbound rules"** button

6. **Add SSH Rule:**
   - Click "Add rule"
   - Type: **SSH**
   - Protocol: **TCP**
   - Port range: **22**
   - Source: **Anywhere IPv4** (0.0.0.0/0) or your IP (safer)
   - Click "Save rules"

7. **Wait 10 seconds for rule to apply**

8. **Come back here and tell me when done**

---

## ALTERNATIVE: Use EC2 Instance Connect (No SSH needed)

If you want to avoid fixing security groups:

1. Go to EC2 Console
2. Select your instance
3. Click "Connect" button (top right)
4. Choose "EC2 Instance Connect" tab
5. Click "Connect"
6. Browser terminal opens - you can run commands directly!

---

## ONCE SECURITY GROUP IS FIXED:

Run this to deploy everything:

```
ssh -i "c:\Users\ADMIN\eval\evaluation\edulytics-key.pem" ubuntu@3.107.105.79 "cd /home/ubuntu/edulytics && source venv/bin/activate && sudo systemctl start gunicorn && sudo systemctl start nginx && echo 'App deployed!'"
```

Then access:
```
http://3.107.105.79/login/
```

---

**Let me know when security group is fixed!**
