from main.models import EvaluationPeriod, Evaluation

# Check student_upward periods
periods = EvaluationPeriod.objects.filter(evaluation_type='student_upward')
print(f"Total student_upward periods: {periods.count()}")

active_period = periods.filter(is_active=True).first()
if active_period:
    print(f"Active period: {active_period.name} (ID: {active_period.id})")
else:
    print("No active student_upward period found")

# Check evaluations
evals = Evaluation.objects.filter(evaluation_type='student_upward')
print(f"\nTotal student_upward evaluations: {evals.count()}")
for e in evals:
    print(f"  - Evaluator: {e.evaluator}, Released: {e.is_released}, Period: {e.evaluation_period}")

# Check context
if active_period:
    released = Evaluation.objects.filter(
        evaluation_type='student_upward',
        evaluation_period=active_period,
        is_released=True
    ).exists()
    print(f"\nstudent_upward_evaluation_active should be: {released}")
else:
    print("\nstudent_upward_evaluation_active should be: False (no active period)")
