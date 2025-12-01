import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'evaluationWeb.settings')
django.setup()

from main.models import IrregularEvaluation, UserProfile

print("Checking IrregularEvaluation records in database...")
print("=" * 60)

# Count total irregular evaluations
total_count = IrregularEvaluation.objects.count()
print(f"\nTotal IrregularEvaluation records: {total_count}")

if total_count > 0:
    print("\nIrregular Evaluations:")
    for eval in IrregularEvaluation.objects.all().select_related('evaluator', 'evaluatee', 'evaluation_period'):
        print(f"\n  ID: {eval.id}")
        print(f"  Evaluator: {eval.evaluator.username}")
        print(f"  Evaluatee: {eval.evaluatee.username}")
        print(f"  Period: {eval.evaluation_period}")
        print(f"  Submitted: {eval.submitted_at}")
else:
    print("\n⚠️ No irregular evaluation records found in database")

print("\n" + "=" * 60)
print("\nChecking irregular students...")
irregular_students = UserProfile.objects.filter(is_irregular=True)
print(f"Total irregular students: {irregular_students.count()}")

if irregular_students.exists():
    for student in irregular_students:
        print(f"  - {student.user.username} ({student.user.email})")
else:
    print("  No irregular students found")
