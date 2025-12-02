"""
Fix script to update get_section_scores to only look at past periods
"""
import re

with open('main/views.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Old pattern - looks for any inactive period
old_pattern = r"# Get the most recent INACTIVE period \(last completed evaluation\)\s+# Results are stored in EvaluationResult when period ends \(unrelease\)\s+latest_period = EvaluationPeriod\.objects\.filter\(\s+evaluation_type='student',\s+is_active=False\s+\)\.order_by\('-end_date'\)\.first\(\)"

# New pattern - only looks at periods that have already ended (in the past)
new_pattern = """# Get the most recent INACTIVE period that has actually ended (not future periods)
        # Results are stored in EvaluationResult when period ends (unrelease)
        from django.utils import timezone
        latest_period = EvaluationPeriod.objects.filter(
            evaluation_type='student',
            is_active=False,
            end_date__lte=timezone.now()  # Only past periods
        ).order_by('-end_date').first()"""

# Replace all occurrences (should be 3: Dean, Coordinator, Faculty)
new_content, count = re.subn(old_pattern, new_pattern, content, flags=re.MULTILINE)

if count > 0:
    print(f"✅ Found and updated {count} instances")
    with open('main/views.py', 'w', encoding='utf-8') as f:
        f.write(new_content)
    print("✅ File updated successfully")
else:
    print("❌ Pattern not found - trying alternative approach")
    
    # Try simpler pattern
    simple_pattern = r"latest_period = EvaluationPeriod\.objects\.filter\(\s+evaluation_type='student',\s+is_active=False\s+\)\.order_by\('-end_date'\)\.first\(\)"
    
    simple_new = """from django.utils import timezone
        latest_period = EvaluationPeriod.objects.filter(
            evaluation_type='student',
            is_active=False,
            end_date__lte=timezone.now()  # Only past periods
        ).order_by('-end_date').first()"""
    
    new_content, count = re.subn(simple_pattern, simple_new, content, flags=re.MULTILINE)
    
    if count > 0:
        print(f"✅ Found and updated {count} instances (simple pattern)")
        with open('main/views.py', 'w', encoding='utf-8') as f:
            f.write(new_content)
        print("✅ File updated successfully")
    else:
        print("❌ Still no matches - need manual fix")
