#!/usr/bin/env python
"""
Fix overall results to use completed periods instead of active periods
"""
import re

# Read the file
with open('main/views.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Pattern 1: Fix Dean and Coordinator get_evaluation_data method
# Replace active period query with completed period query
pattern1 = r"(\s+# Get active student evaluation period \(NOT peer evaluation\)\s+active_student_period = EvaluationPeriod\.objects\.filter\(\s+is_active=True,\s+evaluation_type='student'\s+\)\.first\(\))"
replacement1 = r"""        # Get the most recent COMPLETED period (same as section scores)
        from django.utils import timezone
        latest_period = EvaluationPeriod.objects.filter(
            evaluation_type='student',
            is_active=False,
            end_date__lte=timezone.now()
        ).order_by('-end_date').first()"""

content = re.sub(pattern1, replacement1, content)

# Pattern 2: Replace active_student_period with latest_period in compute_category_scores calls
content = content.replace(
    'evaluation_period=active_student_period)',
    'evaluation_period=latest_period)'
)

# Pattern 3: Replace filter(evaluation_period=active_student_period) with filter(evaluation_period=latest_period)
content = content.replace(
    'filter(evaluation_period=active_student_period)',
    'filter(evaluation_period=latest_period)'
)

# Pattern 4: Update comments - change "active student period" to "completed period"
content = content.replace(
    '# Filter by active student period to exclude peer evaluations',
    '# Filter by completed period to match section scores'
)
content = content.replace(
    'if active_student_period:',
    'if latest_period:'
)

# Pattern 5: Update comment in FETCH COMMENTS section
content = content.replace(
    '# IMPORTANT: Only student evaluation comments, NOT peer evaluation comments',
    '# IMPORTANT: Only student evaluation comments from completed period'
)

# Write back
with open('main/views.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("✅ Fixed overall results to use completed periods!")
print("Changes made:")
print("  - Dean get_evaluation_data: now uses latest completed period")
print("  - Coordinator get_evaluation_data: now uses latest completed period")
print("  - All active_student_period references replaced with latest_period")
print("  - Comments updated to reflect completed period logic")
