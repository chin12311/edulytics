import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'evaluationWeb.settings')
django.setup()

from main.models import IrregularEvaluation

ie = IrregularEvaluation.objects.first()
if ie:
    print("\n=== Irregular Evaluation Data ===")
    print(f"Evaluator: {ie.evaluator.username}")
    print(f"Evaluatee: {ie.evaluatee.username}")
    print(f"\nSample Questions:")
    print(f"  Question 1 (Cat A): {ie.question1}")
    print(f"  Question 7 (Cat B): {ie.question7}")
    print(f"  Question 13 (Cat C): {ie.question13}")
    print(f"  Question 17 (Cat D): {ie.question17}")
    print(f"\nAll Questions:")
    for i in range(1, 20):
        val = getattr(ie, f'question{i}')
        print(f"  Q{i}: {val}")
else:
    print("No irregular evaluations found")
