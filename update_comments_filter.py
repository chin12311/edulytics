"""
Script to add evaluation_period filtering to all comments queries
"""
import re

# Read the file
with open('main/views.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Pattern to find comments_queryset assignments that need updating
old_pattern = r'''comments_queryset = EvaluationResponse\.objects\.filter\(
                evaluatee=user,
                student_section=section_code,
                comments__isnull=False
            \)\.exclude\(comments=''\)'''

# New pattern with evaluation_period filtering
new_pattern = '''# Fetch student comments for this section, filtered by active evaluation period
            comments_filter = {
                'evaluatee': user,
                'student_section': section_code,
                'comments__isnull': False
            }
            
            # Filter by evaluation period if there's an active one
            if active_period:
                comments_filter['evaluation_period'] = active_period
            
            comments_queryset = EvaluationResponse.objects.filter(
                **comments_filter
            ).exclude(comments='')'''

# Count matches
matches = re.findall(old_pattern, content, re.MULTILINE)
print(f"Found {len(matches)} matches to update")

# Replace
content = re.sub(old_pattern, new_pattern, content, flags=re.MULTILINE)

# Also need to add active_period retrieval to get_section_scores methods
# Find all get_section_scores methods and add the active_period line after the docstring

pattern_get_scores = r'(def get_section_scores\(self, user, assigned_sections\):\s+""".*?"""\s+section_scores = {})'

def add_active_period(match):
    return match.group(1) + '\n        \n        # Get current active evaluation period for filtering comments\n        active_period = EvaluationPeriod.objects.filter(is_active=True, evaluation_type=\'student\').first()'

content = re.sub(pattern_get_scores, add_active_period, content, flags=re.DOTALL)

# Write back
with open('main/views.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Updated views.py with evaluation_period filtering for comments")
