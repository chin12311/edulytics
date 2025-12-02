"""
Fix compute_category_scores calls in profile settings views to pass evaluation_period parameter
"""

import re

# Read the file
with open('main/views.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Pattern 1: Fix compute_category_scores(user, section_code) calls
# This appears in get_section_scores() and get_evaluation_data() methods
pattern1 = r'category_scores = compute_category_scores\(user, section_code\)'
replacement1 = 'category_scores = compute_category_scores(user, section_code, evaluation_period=active_period)'
replacement2 = 'category_scores = compute_category_scores(user, section_code, evaluation_period=active_student_period)'

# First, let's find all occurrences and their contexts
lines = content.split('\n')
changes_made = []

for i, line in enumerate(lines):
    if 'category_scores = compute_category_scores(user, section_code)' in line:
        # Check context to determine which replacement to use
        # Look back to find which method we're in
        method_context = '\n'.join(lines[max(0, i-20):i])
        
        if 'def get_section_scores' in method_context:
            # Use active_period (already available in this method)
            lines[i] = line.replace(
                'category_scores = compute_category_scores(user, section_code)',
                'category_scores = compute_category_scores(user, section_code, evaluation_period=active_period)'
            )
            changes_made.append(f"Line {i+1}: get_section_scores() - Changed to use evaluation_period=active_period")
        elif 'def get_evaluation_data' in method_context:
            # Use active_student_period (already available in this method)
            lines[i] = line.replace(
                'category_scores = compute_category_scores(user, section_code)',
                'category_scores = compute_category_scores(user, section_code, evaluation_period=active_student_period)'
            )
            changes_made.append(f"Line {i+1}: get_evaluation_data() - Changed to use evaluation_period=active_student_period")

# Pattern 2: Fix evaluation_count queries to filter by active period
# This appears right after the compute_category_scores call in get_section_scores()
pattern2 = r'''            # Get evaluation count for this section
            evaluation_count = EvaluationResponse\.objects\.filter\(
                evaluatee=user,
                student_section=section_code
            \)\.count\(\)'''

replacement_pattern2 = '''            # Get evaluation count for this section filtered by active period
            evaluation_count_filter = {
                'evaluatee': user,
                'student_section': section_code
            }
            if active_period:
                evaluation_count_filter['submitted_at__gte'] = active_period.start_date
                evaluation_count_filter['submitted_at__lte'] = active_period.end_date
            evaluation_count = EvaluationResponse.objects.filter(**evaluation_count_filter).count()'''

content_updated = '\n'.join(lines)

# Now fix the evaluation_count queries
# This is more complex, so let's do it carefully
old_pattern = '''            # Get evaluation count for this section
            evaluation_count = EvaluationResponse.objects.filter(
                evaluatee=user,
                student_section=section_code
            ).count()'''

new_pattern = '''            # Get evaluation count for this section filtered by active period
            evaluation_count_filter = {
                'evaluatee': user,
                'student_section': section_code
            }
            if active_period:
                evaluation_count_filter['submitted_at__gte'] = active_period.start_date
                evaluation_count_filter['submitted_at__lte'] = active_period.end_date
            evaluation_count = EvaluationResponse.objects.filter(**evaluation_count_filter).count()'''

# Count how many times we'll replace
count = content_updated.count(old_pattern)
content_updated = content_updated.replace(old_pattern, new_pattern)
changes_made.append(f"Fixed {count} evaluation_count queries to filter by active period")

# Also fix the "Get actual evaluation count" variant in Faculty view
old_pattern_faculty = '''            # Get actual evaluation count for this section
            evaluation_count = EvaluationResponse.objects.filter(
                evaluatee=user,
                student_section=section_code
            ).count()'''

new_pattern_faculty = '''            # Get actual evaluation count for this section filtered by active period
            evaluation_count_filter = {
                'evaluatee': user,
                'student_section': section_code
            }
            if active_period:
                evaluation_count_filter['submitted_at__gte'] = active_period.start_date
                evaluation_count_filter['submitted_at__lte'] = active_period.end_date
            evaluation_count = EvaluationResponse.objects.filter(**evaluation_count_filter).count()'''

count_faculty = content_updated.count(old_pattern_faculty)
content_updated = content_updated.replace(old_pattern_faculty, new_pattern_faculty)
if count_faculty > 0:
    changes_made.append(f"Fixed {count_faculty} Faculty evaluation_count queries to filter by active period")

# Write the updated content
with open('main/views.py', 'w', encoding='utf-8') as f:
    f.write(content_updated)

print("✅ FIXES APPLIED SUCCESSFULLY!")
print("\nChanges made:")
for change in changes_made:
    print(f"  • {change}")
