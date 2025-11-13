# Peer Evaluation Fix - Test Guide

## Problem Statement
When Dean tries to access the staff evaluation form after Admin releases evaluations, they get "No active peer evaluation" error instead of the form.

## Root Cause
The evaluation form view was checking for evaluation records in the wrong order and wasn't properly verifying that the peer evaluation period was active and linked to a released evaluation record.

## Changes Made

### 1. **evaluation_form_staffs View (main/views.py, lines ~2180-2230)**
- **Changed:** Reordered checks to verify active peer period FIRST
- **Why:** An active evaluation period must exist before checking for a released evaluation record
- **Added:** Detailed logging to help diagnose issues
- **Benefits:** Clear error messages and better troubleshooting

### 2. **release_peer_evaluation Function (main/views.py, lines ~1805-1875)**
- **Changed:** Smarter cleanup - only deletes unreleased records from OLD periods
- **Previous:** Deleted ALL peer evaluation records (too aggressive)
- **Now:** Preserves historical data, creates fresh record for new active period
- **Benefits:** Data preservation + clean state for new evaluations

## Step-by-Step Testing

### **Setup Phase**
1. Open Django application in browser: `http://localhost:8000`
2. Ensure you have at least 2 admin/staff accounts:
   - **Account 1:** Admin (superuser) - for releasing evaluations
   - **Account 2:** Dean - for accessing evaluations

---

### **Test 1: Admin Releases Evaluations**

**Steps:**
1. Login as **Admin** (superuser)
2. Navigate to: `/evaluationconfig/`
3. Click button: **"🚀 Release All Evaluations"**
4. Verify you see success alerts:
   - "✅ Both Student and Peer Evaluations Released!"

**Expected Result:**
- ✅ Release button becomes disabled
- ✅ Unrelease button becomes enabled
- ✅ Success message shows briefly (3 seconds) and fades

**If this fails:**
- Check browser console (F12) for JavaScript errors
- Check Django terminal logs for backend errors
- Database might not have proper tables

---

### **Test 2: Dean Accesses Staff Evaluation Form**

**Steps:**
1. Logout from Admin
2. Login as **Dean**
3. Go to **Dashboard** or **Home page**
4. Click: **"Start Evaluation"** button
5. Select/click: **"Staff Evaluation"** OR similar peer evaluation option

**Expected Result:**
- ✅ Staff Peer Evaluation Form loads with:
  - Form header: "👥 Staff Peer Evaluation Form"
  - Dropdown to select a colleague
  - Rating scale guide (1-5)
  - Multiple question categories:
    - Communication & Collaboration (Questions 1-6)
    - Responsibility & Professionalism (Questions 7-9)
    - Leadership & Work Ethic (Questions 10-11)
  - Comments section
  - Submit button

**If "No active peer evaluation" error appears:**
- Check Django logs (terminal) for detailed error messages
- Error messages will show like:
  - `❌ No active peer evaluation period found!`
  - `❌ No released peer evaluation record found for period X`

---

### **Test 3: Dean Completes Peer Evaluation**

**Steps:**
1. On the Staff Evaluation form:
2. Select a colleague from dropdown
3. Rate them on all questions (1-5 scale)
4. Add optional comments
5. Click: **"🚀 Submit Evaluation"**

**Expected Result:**
- ✅ Success message: "Evaluation submitted successfully"
- ✅ Redirected back to dashboard/evaluation page
- ✅ Can select a different colleague and evaluate again (if multiple available)

**If submission fails:**
- Check for validation errors
- Ensure all questions are answered (they're required)
- Check Django logs for database errors

---

### **Test 4: Admin Unreleases Evaluations**

**Steps:**
1. Login as **Admin**
2. Go to: `/evaluationconfig/`
3. Click: **"⛔ Unrelease All Evaluations"**
4. Verify success alert

**Expected Result:**
- ✅ Unrelease button becomes disabled
- ✅ Release button becomes enabled
- ✅ Success message appears and fades

**Then:**
5. Logout and login as Dean
6. Try to access Staff Evaluation form again
7. Should see "No active peer evaluation" error

---

## Debugging Logs

The system now has detailed logging. Check the Django terminal for these patterns:

### **Success Indicators:**
```
🔹 Starting release_peer_evaluation...
✅ Archived X previous peer evaluation period(s)
✅ Created new peer evaluation period: Y - Peer Evaluation November 2025
🗑️  Cleaned up X old unreleased peer evaluation record(s)
✅ Created fresh peer evaluation record: Z for period Y
✅ Verification - Peer eval exists with correct period: True
📊 Status: Student Released=True, Peer Released=True
```

### **Error Indicators:**
```
❌ No active peer evaluation period found!
❌ No released peer evaluation record found for period X
❌ Peer evaluation was not created successfully!
```

---

## Expected Database State After Release

After successful release:

**EvaluationPeriod table:**
- New record created: `is_active=True`, `evaluation_type='peer'`
- Old record(s) updated: `is_active=False`

**Evaluation table:**
- New peer record created: `is_released=True`, `evaluation_type='peer'`, `evaluation_period=<new period ID>`

**EvaluationResponse table:**
- Should be empty at this point (no evaluations submitted yet)

---

## Troubleshooting Checklist

- [ ] Django server running and accessible at `http://localhost:8000`
- [ ] Admin account exists with superuser privileges
- [ ] Dean account exists with `role=DEAN` in UserProfile
- [ ] Both accounts are in the same institute
- [ ] Database migrations are up to date
- [ ] No database locks or transaction issues
- [ ] Browser cache cleared (if needed)
- [ ] JavaScript enabled in browser

---

## Success Criteria

✅ All tests pass:
1. Admin can release evaluations
2. Dean sees evaluation form (not error)
3. Dean can select colleague and submit evaluation
4. Admin can unrelease evaluations
5. After unrelease, Dean sees "No active" error again

If all above pass, the fix is **COMPLETE** and **WORKING**! 🎉
