#!/usr/bin/env python
"""
Simple Gmail test - directly test SMTP connection
"""

import smtplib
import os

print("\n" + "="*80)
print("DIRECT GMAIL SMTP TEST")
print("="*80)

# Test credentials
email = 'ccaedulytics@gmail.com'
password = 'vbxlxucdamjcewfn'  # Your app password

print(f"\n📧 Email: {email}")
print(f"🔐 Password: {'*' * len(password)}")

print("\nAttempting to connect to Gmail SMTP...")
print("Host: smtp.gmail.com:587")
print("TLS: Enabled\n")

try:
    # Create SMTP connection
    server = smtplib.SMTP('smtp.gmail.com', 587)
    print("✅ Connected to SMTP server")
    
    # Start TLS
    server.starttls()
    print("✅ TLS enabled")
    
    # Try to login
    server.login(email, password)
    print("✅ LOGIN SUCCESSFUL!")
    print("\n" + "="*80)
    print("✅ YOUR EMAIL CONFIGURATION IS CORRECT!")
    print("="*80)
    print("\nThe app password works. You should now receive emails when you:")
    print("1. Release an evaluation")
    print("2. Send a test email")
    print("\nTry releasing an evaluation again in your admin panel.")
    print("Check your email in 1-2 minutes.\n")
    
    server.quit()
    
except smtplib.SMTPAuthenticationError as e:
    print(f"❌ LOGIN FAILED")
    print(f"Error: {e}")
    print("\nThis means either:")
    print("1. The app password is incorrect")
    print("2. The app password expired")
    print("3. The email address is wrong")
    print("\nTry regenerating the app password at:")
    print("https://myaccount.google.com/apppasswords")
    print("Make sure to:")
    print("- Select 'Mail' app")
    print("- Select 'Windows Computer'")
    print("- Copy the NEW 16-character password (no spaces)")
    print("- Update .env with the new password")
    
except Exception as e:
    print(f"❌ CONNECTION ERROR")
    print(f"Error: {e}")
    print("\nThis could be a network issue or Gmail configuration issue.")

print("="*80 + "\n")
