import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'evaluationWeb.settings')
django.setup()

from django.contrib.auth.models import User
from main.models import SectionAssignment, IrregularEvaluation
from django.db.models import Q

# Check jadepuno's data
user = User.objects.get(username='jadepuno')
profile = user.profile if hasattr(user, 'profile') else None
role = profile.role if profile else 'No role'
print(f"\n=== User: {user.username} ({role}) ===")

# Check sections
assignments = SectionAssignment.objects.filter(user=user)
print(f"\nAssigned Sections: {assignments.count()}")
for assignment in assignments:
    print(f"  - {assignment.section.code} (ID: {assignment.section.id})")

# Check irregular evaluations
irregular = IrregularEvaluation.objects.filter(evaluatee=user)
print(f"\nIrregular Evaluations: {irregular.count()}")
for ie in irregular:
    print(f"  - From: {ie.evaluator.username}")
    print(f"    Q1: {ie.question1}, Q7: {ie.question7}")

print("\n=== Expected Dropdown Items (HTML) ===")
print("1. Overall Results (class='overall-option' data-section='overall')")
print("2. Peer Evaluation (class='peer-option' data-section='peer')")
print("3. Irregular Evaluations (class='irregular-option' data-section='irregular')")
for assignment in assignments:
    print(f"4. Section {assignment.section.code} (class='section-item' data-section='{assignment.section.id}')")

print("\n=== JavaScript Selector ===")
print("querySelectorAll('.section-item, .overall-option, .peer-option, .irregular-option')")
print(f"Expected to find: {3 + assignments.count()} elements")

print("\n=== Check Template Has Data ===")
print("View should pass these to template:")
print(f"  - assigned_sections: {assignments.count()} items")
print(f"  - irregular_scores_json: should have has_data=True")
print(f"  - timestamp: should be a Unix timestamp")
