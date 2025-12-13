# Dean Evaluation - Admin Quick Start Guide

## What is Dean Evaluation?
Faculty members evaluate their dean's leadership and management performance using 15 standardized questions.

## How to Release Dean Evaluation

### Step 1: Access Admin Panel
1. Login as administrator
2. Navigate to **Manage Evaluations** page

### Step 2: Find Dean Evaluation Section
Look for the "Dean Evaluation" container (similar to Upward Evaluation)

### Step 3: Release Evaluation
1. Click **"Release Dean Evaluation"** button
2. System will:
   - Archive previous dean evaluation results to history
   - Create new evaluation period (e.g., "Dean Evaluation 2025-12-13 15:30:00")
   - Set evaluation status to "Released" and "Active"
   - Send email notification to all faculty members
3. Success message will show:
   - Number of archived results
   - New evaluation period name
   - Number of emails sent to faculty

### Step 4: Monitor Progress
- Faculty can now evaluate their dean
- Each faculty member can evaluate their institute's dean once per period
- System prevents duplicate evaluations automatically

## How to Unrelease (Close) Dean Evaluation

### Step 1: End Evaluation Period
1. Click **"Unrelease Dean Evaluation"** button
2. System will:
   - Process all dean evaluation responses
   - Calculate average scores for each dean
   - Create EvaluationResult records (admin-only visible)
   - Set evaluation period to "Inactive"
   - Send closure email to all faculty members

### Step 2: View Results
1. Navigate to **Evaluation Results** page
2. Filter by:
   - Evaluation Type: "Dean"
   - Evaluation Period: Select the closed period
3. View dean performance scores and faculty feedback

## Important Notes

### Who Can Evaluate?
- **Faculty only** can evaluate deans
- Each faculty member evaluates their own institute's dean
- One evaluation per faculty per dean per period

### Evaluation Questions
Faculty rate their dean on 15 questions covering:
- **Mission**: Commitment to institutional mission and vision (3 questions)
- **Communion**: Collaboration and communication (3 questions)
- **Excellence**: Academic and administrative standards (4 questions)
- **Innovation**: Support for innovation and research (3 questions)
- **Leadership**: Leadership and management skills (2 questions)

### Rating Scale
- Strongly Disagree (1 point)
- Disagree (2 points)
- Neutral (3 points)
- Agree (4 points)
- Strongly Agree (5 points)

### Scoring
- Maximum score: 75 points (15 questions × 5 points)
- Final result: Percentage (0-100%)
- Higher percentage = Better performance

### Email Notifications
- **Release**: Faculty receive "Dean Evaluation Form Released" email
- **Close**: Faculty receive "Dean Evaluation Period Closed" email
- Sent to: All active faculty members only

## Faculty User Experience

### How Faculty Access Dean Evaluation
1. Login to system
2. Click **"Upward Evaluation"** in left sidebar
3. Read and check terms agreement box
4. Click **"Start Dean Evaluation"** button (green)
5. Select their dean from dropdown
6. Complete 15 evaluation questions
7. Add optional comments
8. Click **"Submit Evaluation"**
9. See confirmation message

### Faculty View
- Faculty see list of deans from their institute only
- Deans already evaluated show "Already Evaluated" badge
- Cannot submit duplicate evaluations
- Can evaluate multiple deans if institute has multiple deans (rare)

## Troubleshooting

### "Dean evaluation is already released"
- A dean evaluation period is already active
- Close the current period before starting a new one

### "No active dean evaluation period found"
- No dean evaluation is currently released
- Release a new evaluation period first

### Faculty reports "No dean to evaluate"
- Check if dean is assigned to faculty's institute
- Verify dean's role is set to "Dean" in user profile
- Ensure dean's institute matches faculty's institute

### No email received
- Check email configuration in settings.py
- Verify faculty have valid email addresses
- Check spam/junk folders

## Best Practices

### Timing
- Run dean evaluation **once per semester** or **once per year**
- Give faculty **2-4 weeks** to complete evaluations
- Send reminder before closing period

### Communication
- Announce evaluation period to faculty
- Explain importance of honest feedback
- Emphasize anonymity (admin sees aggregated results only)

### Results Review
- Review results privately
- Discuss with deans confidentially
- Use results for professional development planning
- Never publicly share individual dean scores

### Archive Management
- System automatically archives old results before new period
- Previous results remain in EvaluationHistory table
- Access history through admin panel if needed

## Admin Panel Quick Actions

```
✅ Release Dean Evaluation
   → Start new evaluation period
   → Faculty can now evaluate

✅ Unrelease Dean Evaluation  
   → End evaluation period
   → Process results
   → Faculty can no longer evaluate

✅ View Results
   → Navigate to Evaluation Results page
   → Filter by "Dean" type
   → Review dean performance scores
```

## Support Contact
For technical issues or questions:
- Contact system administrator
- Email: cibituonon@cca.edu.ph
- Check system logs for error details

---

**Quick Reference Card**

| Action | Button | Result |
|--------|--------|--------|
| Start dean evaluation | Release Dean Evaluation | Faculty can evaluate deans |
| End dean evaluation | Unrelease Dean Evaluation | Results processed, period closed |
| View results | Evaluation Results page | See dean performance scores |
| Check who evaluated | Admin Panel → Dean Evaluation Responses | See all submissions |

**Evaluation Cycle**: Release → Faculty Evaluate → Unrelease → Review Results → Archive → Repeat

**Frequency**: Once per semester or year (recommended)

**Duration**: 2-4 weeks (recommended)
