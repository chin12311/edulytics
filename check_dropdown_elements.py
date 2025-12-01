import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'evaluation.settings')
django.setup()

from django.contrib.auth.models import User
from main.models import SectionAssignment

# Check jadepuno's sections
user = User.objects.get(username='jadepuno')
assignments = SectionAssignment.objects.filter(user=user)

print(f"\n=== User: {user.username} ({user.role}) ===")
print(f"Assigned Sections: {assignments.count()}")

for assignment in assignments:
    print(f"\n  Section: {assignment.section.code}")
    print(f"  Section ID: {assignment.section.id}")
    print(f"  Year Level: {assignment.section.year_level}")

print("\n=== Expected Dropdown Items ===")
print("1. Overall Option (data-section='overall')")
print("2. Peer Option (data-section='peer')")
print("3. Irregular Option (data-section='irregular')")
for assignment in assignments:
    print(f"4. Section {assignment.section.code} (data-section='{assignment.section.id}')")

print("\n=== JavaScript Selector ===")
print("querySelectorAll('.section-item, .overall-option, .peer-option, .irregular-option')")
print(f"Should find: {3 + assignments.count()} items")

# Check if irregular scores exist
from main.models import IrregularEvaluation
irregular = IrregularEvaluation.objects.filter(evaluatee=user)
print(f"\n=== Irregular Evaluations ===")
print(f"Count: {irregular.count()}")
for ie in irregular:
    print(f"  From: {ie.evaluator.username} → {ie.evaluatee.username}")
