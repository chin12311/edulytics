from main.models import Evaluation, EvaluationPeriod

print("=" * 80)
print("EVALUATION STATUS CHECK")
print("=" * 80)

# Check Evaluation records
print("\n📋 EVALUATION RECORDS:")
student_evals = Evaluation.objects.filter(evaluation_type='student')
print(f"Total student evaluation records: {student_evals.count()}")
for eval in student_evals:
    print(f"  ID: {eval.id} | Released: {eval.is_released} | Period: {eval.evaluation_period}")

peer_evals = Evaluation.objects.filter(evaluation_type='peer')
print(f"\nTotal peer evaluation records: {peer_evals.count()}")
for eval in peer_evals:
    print(f"  ID: {eval.id} | Released: {eval.is_released} | Period: {eval.evaluation_period}")

# Check EvaluationPeriod
print("\n📅 EVALUATION PERIODS:")
student_periods = EvaluationPeriod.objects.filter(evaluation_type='student')
print(f"Total student periods: {student_periods.count()}")
for period in student_periods:
    status = "🟢 ACTIVE" if period.is_active else "🔴 INACTIVE"
    print(f"  {status} | {period.name} (ID: {period.id})")

peer_periods = EvaluationPeriod.objects.filter(evaluation_type='peer')
print(f"\nTotal peer periods: {peer_periods.count()}")
for period in peer_periods:
    status = "🟢 ACTIVE" if period.is_active else "🔴 INACTIVE"
    print(f"  {status} | {period.name} (ID: {period.id})")

print("\n" + "=" * 80)
