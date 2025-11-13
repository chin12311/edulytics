# 📋 Admin Question Management - User Guide with Screenshots

## 🎯 Quick Navigation

### How to Access
```
1. Login to System (as Admin)
   ↓
2. Click "Admin Control Panel" button
   ↓
3. Look for "📋 Manage Questions" button
   ↓
4. Click to open Question Management Interface
```

---

## 🖥️ Interface Layout

### Main Management Page

```
┌─────────────────────────────────────────────────────────┐
│  📋 Manage Evaluation Questions                          │
│  [↻ Reset to Defaults]                                  │
├─────────────────────────────────────────────────────────┤
│                                                           │
│  [👨‍🎓 Student Evaluation (19)] [👥 Peer Evaluation (11)]  │
│                                                           │
│  ┌─────────────────────────────────────────────────────┐ │
│  │ Question 1                                          │ │
│  │ How well does the teacher demonstrate subject      │ │
│  │ matter expertise?                                  │ │
│  │                                        [Edit]      │ │
│  ├─────────────────────────────────────────────────────┤ │
│  │ Question 2                                          │ │
│  │ How effectively does the teacher use instructional │ │
│  │ techniques?                                         │ │
│  │                                        [Edit]      │ │
│  ├─────────────────────────────────────────────────────┤ │
│  │ [... more questions ...]                           │ │
│  └─────────────────────────────────────────────────────┘ │
│                                                           │
│  ┌─────────────────────────────────────────────────────┐ │
│  │                                                       │ │
│  │             [💾 Save All Changes]                   │ │
│  │         [← Back to Admin Panel]                     │ │
│  │                                                       │ │
│  └─────────────────────────────────────────────────────┘ │
│                                                           │
└─────────────────────────────────────────────────────────┘
```

---

## 📝 Edit Question Modal

### When You Click "Edit"

```
┌─────────────────────────────────────────────────────────┐
│ ✕                                                        │
│                  Edit Question                           │
├─────────────────────────────────────────────────────────┤
│                                                           │
│ Question Text:                                           │
│ ┌─────────────────────────────────────────────────────┐ │
│ │ How well does the teacher demonstrate subject       │ │
│ │ matter expertise?                                   │ │
│ │                                                     │ │
│ └─────────────────────────────────────────────────────┘ │
│                                                           │
│ ☑ Active                                                 │
│                                                           │
│ ┌──────────────────┐ ┌──────────────────┐             │ │
│ │  💾 Save         │ │  Cancel          │             │ │
│ └──────────────────┘ └──────────────────┘             │ │
│                                                           │
└─────────────────────────────────────────────────────────┘
```

---

## 🔄 Workflow Examples

### Example 1: Edit Single Question

```
STEP 1: View Questions
┌────────────────────────┐
│ Student Questions Tab  │ ← SELECT THIS
│ Peer Questions Tab     │
└────────────────────────┘

STEP 2: Find Question
┌────────────────────────────────────────────┐
│ Q3: How effectively does the teacher       │
│     manage classroom time?                 │
│                                  [Edit]    │ ← CLICK EDIT
└────────────────────────────────────────────┘

STEP 3: Edit in Modal
┌─────────────────────────────────────┐
│ Edit Question                       │
├─────────────────────────────────────┤
│ "How effectively does the teacher  │
│  manage classroom time and          │
│  pacing?"                           │ ← MODIFY TEXT
│                                     │
│ ☑ Active                            │
│                                     │
│ [💾 Save]  [Cancel]                │ ← CLICK SAVE
└─────────────────────────────────────┘

STEP 4: Save All Changes
┌──────────────────────────┐
│ Question updated.        │  ← CONFIRMATION
│ Don't forget to save!    │
└──────────────────────────┘

[💾 Save All Changes] ← CLICK HERE TO SAVE

✅ All changes saved successfully!  ← SUCCESS MESSAGE
```

### Example 2: Edit Multiple Questions

```
STEP 1: Make First Edit
[Edit Q1] → [Update Text] → [Save] → Question highlighted in yellow

STEP 2: Make Second Edit
[Edit Q5] → [Update Text] → [Save] → Question highlighted in yellow

STEP 3: Make Third Edit
[Edit Q12] → [Toggle Active] → [Save] → Question highlighted in yellow

STEP 4: Save All at Once
[💾 Save All Changes]

✅ Successfully updated 3 questions!
   - Question 1 updated
   - Question 5 updated
   - Question 12 updated
```

### Example 3: Reset All to Defaults

```
STEP 1: Click Reset Button
[↻ Reset to Defaults]

STEP 2: Confirm Action
"Are you sure you want to reset all 
questions to default values? 
This cannot be undone."

[Cancel]  [OK] ← CLICK TO CONFIRM

STEP 3: Wait for Processing
[Processing...] ← Page refreshes

✅ All questions reset to defaults!
```

---

## 🎨 Tab Switching

### Student Evaluation Tab (19 Questions)

```
Active Tab:
┌──────────────────────────┬──────────────────┐
│ 👨‍🎓 Student Evaluation   │ Peer Evaluation  │  ← Peer is inactive
│ (19 Questions)           │ (11 Questions)   │
└──────────────────────────┴──────────────────┘
      ↓ Shows:
   Q1: How well does the teacher demonstrate...
   Q2: How effectively does the teacher use...
   Q3: How well does the teacher provide...
   ... (19 total)
```

### Peer Evaluation Tab (11 Questions)

```
Active Tab:
┌──────────────────────────┬──────────────────┐
│ Student Evaluation       │ 👥 Peer         │  ← Now active
│ (19 Questions)           │ Evaluation      │
└──────────────────────────┴──────────────────┘
      ↓ Shows:
   Q1: How well does this colleague demonstrate...
   Q2: How effectively does this colleague...
   Q3: How well does this colleague mentor...
   ... (11 total)
```

---

## ⚡ Features Explained

### Active Toggle
```
☑ Active
  ↓
  Question will appear in evaluation forms

☐ Inactive
  ↓
  Question will NOT appear in forms
  (but data is preserved in database)
```

### Save Buttons

**Individual Save** (in modal):
```
After editing: [💾 Save]
Result: Modal closes, question highlighted
Status: Changes NOT yet saved to database
```

**Bulk Save** (main page):
```
After editing one or more: [💾 Save All Changes]
Result: All changes sent to server
Status: ✅ Changes SAVED to database
```

### Reset Button
```
[↻ Reset to Defaults]
↓
Restore ALL 30 questions to original values
↓
Use if you make mistakes
↓
⚠️  Warning: Cannot undo individually
    You must reset everything or keep changes
```

---

## 💬 Messages & Notifications

### Success Message
```
✅ All changes saved successfully!
```

### Error Messages
```
❌ Question text cannot be empty!
❌ Network error occurred, please try again
❌ You don't have permission to access this page
```

### Loading Indicator
```
[⟳ Saving...] ← Shows while saving
```

---

## 📱 Mobile View

### Mobile Layout
```
┌────────────────────────┐
│ ↰ Back Button           │
├────────────────────────┤
│ 📋 Manage Questions    │
│ [↻ Reset]              │
├────────────────────────┤
│ [👨‍🎓 Student] [👥 Peer]  │
├────────────────────────┤
│ Q1 Text...             │
│ [Edit]                 │
├────────────────────────┤
│ Q2 Text...             │
│ [Edit]                 │
│ [... more ...]         │
├────────────────────────┤
│ [💾 Save All]          │
│ [← Back]               │
└────────────────────────┘
```

---

## 🔐 Permission Denied

### If Not Admin
```
❌ Access Denied

You do not have permission to access this page.

This feature is available to administrators only.

[← Back to Dashboard]
```

---

## 💡 Tips & Tricks

### Tip 1: Save Frequently
- Make a few edits
- Click "Save All Changes"
- Don't make too many changes before saving

### Tip 2: Use Reset Wisely
- Reset only when you've made many mistakes
- Reset restores ALL questions, not just one
- Check confirm dialog carefully

### Tip 3: Check Active Status
- Before saving, verify questions are set correctly
- Active (checked) = will appear in forms
- Inactive (unchecked) = hidden from forms

### Tip 4: Mobile Friendly
- Interface works on phone/tablet
- All buttons are touch-friendly
- Use landscape mode for easier editing

### Tip 5: Audit Trail
- All changes are logged
- Check Activity Log for history
- See who changed what and when

---

## ❓ Troubleshooting

### Q: Changes not showing?
A: Click "Save All Changes" - local edits don't persist until saved

### Q: Accidentally reset?
A: Contact admin - backups exist if needed

### Q: Can't access page?
A: Verify you're logged in as admin

### Q: Form shows old questions?
A: Refresh browser (Ctrl+F5 or Cmd+Shift+R)

### Q: Modal won't open?
A: Try different browser, check internet connection

---

## 🎓 Quick Reference

| Task | Steps |
|------|-------|
| **View questions** | Click "Manage Questions" → Choose tab |
| **Edit question** | Click "Edit" → Update text → Click "Save" |
| **Deactivate question** | Click "Edit" → Uncheck "Active" → "Save" |
| **Save changes** | After editing → [💾 Save All Changes] |
| **Reset all** | [↻ Reset to Defaults] → Confirm |
| **Go back** | [← Back to Admin Panel] |
| **Switch tabs** | Click "Student" or "Peer" tab |

---

## ✅ Final Checklist

Before using:
- ☑ Logged in as admin
- ☑ In Admin Control Panel
- ☑ Can see "📋 Manage Questions" button
- ☑ Can see both tabs (Student & Peer)
- ☑ Can see all 30 questions

You're ready to go! 🚀

---

*This guide covers all features of the Question Management Interface*
