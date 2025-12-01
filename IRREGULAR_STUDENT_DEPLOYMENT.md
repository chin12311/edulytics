# Irregular Student Feature - Deployment Guide

## Summary of Changes

This feature adds support for irregular students who don't have assigned sections but need to evaluate all available instructors.

### Files Modified/Created:

1. **main/models.py**
   - Added `is_irregular` BooleanField to UserProfile model
   - Created new `IrregularEvaluation` model (mirrors EvaluationResponse structure)

2. **main/migrations/0018_userprofile_is_irregular_irregularevaluation.py**
   - Database migration to add is_irregular column
   - Creates main_irregularevaluation table

3. **register/templates/register/register.html**
   - Added irregular student toggle switch (ON/OFF)
   - JavaScript to disable section dropdown when irregular is enabled

4. **register/forms.py**
   - Added is_irregular field handling
   - Modified save() to set profile.is_irregular

5. **main/views.py**
   - Modified `EvaluationFormView.get()` to show ALL instructors for irregular students
   - Modified `submit_evaluation()` to route irregular submissions to IrregularEvaluation table
   - Added `get_irregular_evaluation_scores()` method to Dean, Coordinator, and Faculty profile views
   - Added documentation comments to `compute_category_scores()` and `compute_peer_scores()`

6. **main/services/evaluation_service.py**
   - Added documentation comments to `calculate_overall_score()` documenting irregular exclusion

## Deployment Steps

### Step 1: Push Changes to GitHub

Since there are secrets in deployment files preventing push, you have two options:

**Option A: Remove secrets from deployment files first**
```bash
# Remove or gitignore these files:
# - DEPLOY_AWS_QUICK_START.md
# - deploy_aws.sh
# - deploy_to_aws.ps1

git rm --cached DEPLOY_AWS_QUICK_START.md deploy_aws.sh deploy_to_aws.ps1
git commit -m "Remove files with secrets"
git push origin main
```

**Option B: Manually copy files to AWS**
Use SCP or FTP to copy these specific files to AWS:
- main/models.py
- main/migrations/0018_userprofile_is_irregular_irregularevaluation.py
- register/templates/register/register.html
- register/forms.py
- main/views.py
- main/services/evaluation_service.py

### Step 2: SSH to AWS EC2

```bash
ssh -i /path/to/your/aws-key.pem ubuntu@13.211.104.201
```

### Step 3: Navigate to Project Directory

```bash
cd edulytics
```

### Step 4: Pull Latest Changes (if pushed to GitHub)

```bash
git pull origin main
```

### Step 5: Activate Virtual Environment

```bash
source venv/bin/activate
```

### Step 6: Run Migration

```bash
python3 manage.py migrate
```

Expected output:
```
Running migrations:
  Applying main.0018_userprofile_is_irregular_irregularevaluation... OK
```

### Step 7: Verify Database Changes

```bash
python3 manage.py shell
```

Then run:
```python
from main.models import IrregularEvaluation, UserProfile
from django.db import connection

# Check if is_irregular column exists
cursor = connection.cursor()
cursor.execute("DESCRIBE main_userprofile;")
print([row for row in cursor.fetchall() if 'is_irregular' in str(row)])

# Check if main_irregularevaluation table exists
cursor.execute("SHOW TABLES LIKE 'main_irregularevaluation';")
print(cursor.fetchall())

# Exit
exit()
```

### Step 8: Restart Services

```bash
sudo systemctl restart gunicorn
sudo systemctl restart nginx
```

### Step 9: Check Service Status

```bash
sudo systemctl status gunicorn
sudo systemctl status nginx
```

## Testing Steps

### Test 1: Create Irregular Student Account

1. Login as admin at http://13.211.104.201/admin-control/
2. Click "Add Account"
3. Fill in student details
4. Toggle "Irregular Student" switch to ON
5. Notice section dropdown becomes disabled
6. Create account

### Test 2: Login as Irregular Student

1. Logout
2. Login with the irregular student account
3. Navigate to evaluation form
4. Verify you can see ALL instructors (Faculty, Coordinator, Dean) - not just section-assigned ones

### Test 3: Submit Evaluation

1. Select an instructor
2. Fill out evaluation form (19 questions)
3. Submit evaluation
4. Verify success message

### Test 4: Verify Database Storage

```bash
python3 manage.py shell
```

```python
from main.models import IrregularEvaluation, EvaluationResponse

# Check irregular evaluation was saved
irregular_evals = IrregularEvaluation.objects.all()
print(f"Irregular evaluations count: {irregular_evals.count()}")
print(irregular_evals.first().__dict__ if irregular_evals.exists() else "No irregular evaluations")

# Verify it's NOT in regular evaluations
regular_count = EvaluationResponse.objects.filter(evaluator__userprofile__is_irregular=True).count()
print(f"Regular evaluations from irregular students (should be 0): {regular_count}")

exit()
```

### Test 5: Check Instructor Profile

1. Login as the instructor who was evaluated
2. Go to Profile Settings
3. Scroll to "Irregular Student Evaluations" section (below peer evaluations)
4. Verify the evaluation appears with scores

### Test 6: Verify Exclusion from Overall Results

1. Login as admin
2. Process evaluation results
3. Check that irregular evaluations are NOT included in overall scores
4. Verify only regular EvaluationResponse records affect passing/failing determinations

## Rollback Plan

If issues occur:

```bash
# Revert migration
python3 manage.py migrate main 0017

# Rollback git
git reset --hard origin/main

# Restart services
sudo systemctl restart gunicorn
sudo systemctl restart nginx
```

## Feature Specifications

- Irregular students see ALL instructors (Faculty, Coordinator, Dean) excluding Admin
- Irregular evaluations saved to separate `main_irregularevaluation` table
- Irregular evaluations displayed in instructor profiles below peer evaluations
- Irregular evaluations EXCLUDED from:
  - Overall score calculations
  - Pass/fail determinations
  - EvaluationResult records
  - Failure tracking and alerts

## Git Commits

1. `0b70625` - Add irregular student feature (part 1): models, migration, forms, registration UI
2. `3e62fb9` - Modify submit_evaluation to route irregular students to IrregularEvaluation table
3. `62f5b44` - Add irregular evaluation scores display to all profile views (Dean, Coordinator, Faculty)
4. `8e66e9b` - Document irregular evaluation exclusion from overall calculations

## Support

If you encounter issues:
1. Check `sudo tail -f /var/log/gunicorn/error.log`
2. Check `sudo tail -f /var/log/nginx/error.log`
3. Verify migration applied: `python3 manage.py showmigrations main`
4. Test database connection: `python3 manage.py dbshell`
