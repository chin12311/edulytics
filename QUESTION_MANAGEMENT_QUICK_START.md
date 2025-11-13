# Admin Question Management - Quick Start Guide

## 🎯 Quick Summary

Admins can now manage evaluation questions dynamically without code changes:
- **19 Student Evaluation Questions**
- **11 Peer Evaluation Questions**

Both can be edited, updated, and reset through the admin panel.

---

## 🚀 How to Access

1. **Login as Admin**
2. **Go to Admin Control Panel**
3. **Click "📋 Manage Questions" button**

---

## 📝 Managing Questions

### Edit Individual Question
```
1. Click "Edit" button on any question
2. Modal opens with text editor
3. Update the question text
4. Toggle "Active" checkbox if needed
5. Click "Save"
```

### Save All Changes
```
After editing one or more questions:
1. Click "💾 Save All Changes"
2. Server validates and saves
3. Admin activity is logged
4. Toast notification confirms success
```

### Reset All to Defaults
```
1. Click "↻ Reset to Defaults" button
2. Confirm in dialog box
3. All 30 questions restore to original values
4. Action is logged
```

### Switch Between Tabs
```
- Student Evaluation: Shows 19 questions
- Peer Evaluation: Shows 11 questions
- Click tab to switch views
```

---

## 🔑 Key Features

✅ **Intuitive UI** - Easy to find and edit questions  
✅ **Bulk Updates** - Save multiple changes at once  
✅ **Active Toggle** - Enable/disable questions without deletion  
✅ **Reset Option** - Easily restore defaults if mistakes happen  
✅ **Activity Logging** - All changes are tracked  
✅ **Mobile Responsive** - Works on all devices  
✅ **Error Handling** - Clear error messages if something fails  

---

## ⚙️ Technical Details

### Database Structure
```
EvaluationQuestion
├── id (Primary Key)
├── evaluation_type ('student' or 'peer')
├── question_number (1-19 or 1-11)
├── question_text (VARCHAR)
├── is_active (Boolean)
├── created_at (Timestamp)
└── updated_at (Timestamp)

PeerEvaluationQuestion
├── question_number (1-11, Primary Key)
├── question_text (VARCHAR)
├── is_active (Boolean)
├── created_at (Timestamp)
└── updated_at (Timestamp)
```

### API Endpoints

**View All Questions**
```
GET /manage-evaluation-questions/
```

**Update Single Question**
```
POST /update-evaluation-question/<type>/<id>/
Body: {question_text: "...", is_active: true/false}
```

**Bulk Update Questions**
```
POST /bulk-update-evaluation-questions/
Body: {
  question_type: 'student' or 'peer',
  questions: [{id, question_text}, ...]
}
```

**Reset All Questions**
```
POST /reset-evaluation-questions/
```

---

## 🛡️ Security

✅ Admin-only access (checked on all views)  
✅ CSRF token validation on all POST requests  
✅ User permissions verified before allowing changes  
✅ All modifications logged with admin username  

---

## 📊 Current Questions

### Student Evaluation (19 Questions)
1. How well does the teacher demonstrate subject matter expertise?
2. How effectively does the teacher use instructional techniques?
3. How well does the teacher provide constructive feedback?
4. How effectively does the teacher engage students?
5. How well does the teacher facilitate critical thinking?
6. How effectively does the teacher manage classroom time?
7. How well does the teacher assess student understanding?
8. How effectively does the teacher differentiate instruction?
9. How well does the teacher create a supportive classroom environment?
10. How effectively does the teacher communicate expectations?
11. How well does the teacher integrate technology in instruction?
12. How effectively does the teacher encourages student participation?
13. How well does the teacher adapt to different learning styles?
14. How effectively does the teacher provides opportunities for collaboration?
15. How well does the teacher maintains professional behavior?
16. How effectively does the teacher supports student confidence?
17. How well does the teacher connects content to real-world applications?
18. How effectively does the teacher handles diverse student needs?
19. How well would you recommend this teacher to a colleague?

### Peer Evaluation (11 Questions)
1. How well does this colleague demonstrate subject matter expertise?
2. How effectively does this colleague contribute to our school culture?
3. How well does this colleague mentor other teachers?
4. How effectively does this colleague collaborate on projects?
5. How well does this colleague support student success?
6. How effectively does this colleague use evidence-based practices?
7. How well does this colleague communicate professionally?
8. How effectively does this colleague participates in professional development?
9. How well does this colleague manages their professional responsibilities?
10. How effectively does this colleague models ethical behavior?
11. How likely would you recommend this person for leadership roles?

---

## ❓ FAQ

**Q: Can I add new questions?**  
A: The current system uses fixed numbers (19 student, 11 peer). To add new questions, you would need to update the management command. Contact your development team.

**Q: What happens if I deactivate a question?**  
A: Deactivated questions won't be shown in evaluation forms, but the data is preserved in the database.

**Q: Can changes be undone?**  
A: Yes! Use the "Reset to Defaults" button to restore all questions to their original values.

**Q: Are changes logged?**  
A: Yes! All changes are logged in the Admin Activity Log with timestamp and admin username.

**Q: Do I need to restart the server?**  
A: No, changes are effective immediately. Students see updated questions on next page load.

---

## 📞 Support

If you encounter issues:

1. Check that you're logged in as an admin
2. Clear browser cache and refresh
3. Check browser console for JavaScript errors
4. Contact your IT administrator if problems persist

---

*Feature implemented and ready to use!*
