# 📧 How to Generate Gmail App Password for Edulytics

## Step 1: Open Gmail Security Settings

1. **Go to this URL in your browser:**
   ```
   https://myaccount.google.com/apppasswords
   ```
   
   This is the direct link to the App Passwords page.

---

## Step 2: Sign In (if not already signed in)

Make sure you're signed into:
```
Email: edulyticscca@gmail.com
```

If you're signed in as a different account, sign out and sign back in with this email.

---

## Step 3: You'll See This Screen

The page should show you something like this:

```
┌─────────────────────────────────────────────┐
│         App passwords                        │
│                                              │
│  Select the app and device you want an      │
│  app password for.                          │
│                                              │
│  Select app: [▼ Mail         ]               │
│  Select device: [▼ Windows Computer]        │
│                                              │
│                    [Generate]                │
└─────────────────────────────────────────────┘
```

### Click the first dropdown: "Mail"

**BEFORE clicking:**
```
[▼ Select app        ]
```

**AFTER clicking, you'll see options:**
```
[▼ Mail               ]  ← SELECT THIS
  Chrome
  Firefox
  Outlook
  ...
```

### Click the second dropdown: "Windows Computer"

**BEFORE clicking:**
```
[▼ Select device     ]
```

**AFTER clicking, you'll see options:**
```
[▼ Windows Computer  ]  ← SELECT THIS
  iPhone
  iPad
  Android Phone
  Mac
  Linux
  ...
```

---

## Step 4: Click Generate

Once you have:
- ✅ "Mail" selected in first dropdown
- ✅ "Windows Computer" selected in second dropdown

**Click the blue "Generate" button**

---

## Step 5: Copy Your App Password

Google will show you a popup with your 16-character app password:

```
┌───────────────────────────────────────┐
│  Your app password for Mail on         │
│  Windows Computer:                     │
│                                        │
│  ┌────────────────────────────────┐   │
│  │ abcd efgh ijkl mnop            │   │
│  └────────────────────────────────┘   │
│                                        │
│        [Copy]                          │
└───────────────────────────────────────┘
```

Click **[Copy]** to copy it (or manually select and copy the text).

### Important: Remove the Spaces

Google shows it with spaces: `abcd efgh ijkl mnop`

Remove the spaces to get: `abcdefghijklmnop` (16 characters, no spaces)

---

## Step 6: Update Your `.env` File

Find this line in your `.env` file:

```
EMAIL_HOST_PASSWORD=qedtcjktawyidycc
```

Replace it with your new 16-character password:

```
EMAIL_HOST_PASSWORD=<your-16-char-password>
```

Example (don't use this, use YOUR actual password):
```
EMAIL_HOST_PASSWORD=abcdefghijklmnop
```

---

## Step 7: Restart Django and Test

After updating the `.env` file:

1. **Stop Django** (if it's running)
2. **Run the diagnostic:**
   ```powershell
   python troubleshoot_email.py
   ```

3. **You should see:**
   ```
   ✅ Successfully connected to Gmail SMTP
   ✅ Test email sent successfully!
   ```

---

## Troubleshooting

### Problem: "I don't see the App passwords option"

**Solution:** You need to enable 2-Step Verification first
1. Go to: https://myaccount.google.com/security
2. Find "2-Step Verification" 
3. Click "Turn on 2-Step Verification"
4. Follow the prompts
5. Then try https://myaccount.google.com/apppasswords again

### Problem: "I see 'Select app' but no 'Mail' option"

**Solution:** Make sure you have 2-Step Verification enabled (see above)

### Problem: "The password still doesn't work"

**Solution:** 
1. Go back to https://myaccount.google.com/apppasswords
2. Delete the old app password you created
3. Generate a new one
4. Copy it again (making sure to remove spaces)
5. Update `.env` and test again

### Problem: "I don't see 'Windows Computer' in the device dropdown"

**Solution:** Just select whatever device type you're using:
- If on your Windows PC → "Windows Computer"
- If on a Mac → "Mac"
- If on Linux → "Linux"

The exact option doesn't matter too much - what matters is that you're creating an app password.

---

## Summary

| Step | Action |
|------|--------|
| 1 | Go to https://myaccount.google.com/apppasswords |
| 2 | Sign in as edulyticscca@gmail.com |
| 3 | Select "Mail" in first dropdown |
| 4 | Select "Windows Computer" in second dropdown |
| 5 | Click "Generate" |
| 6 | Copy the 16-character password (remove spaces) |
| 7 | Update `.env` file with new password |
| 8 | Run `python troubleshoot_email.py` to verify |

Let me know when you've done this! 🚀
