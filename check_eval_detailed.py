from main.models import Evaluation, EvaluationPeriod
from django.db.models import Q

print("=" * 80)
print("DETAILED EVALUATION STATUS")
print("=" * 80)

# Check all evaluation periods
print("\n📅 ALL EVALUATION PERIODS:")
all_periods = EvaluationPeriod.objects.all().order_by('-start_date')
for period in all_periods[:10]:
    status = "🟢 ACTIVE" if period.is_active else "🔴 INACTIVE"
    print(f"  {status} | {period.evaluation_type.upper():8} | {period.name} | Start: {period.start_date}")

# Check student evaluation status
print("\n📚 STUDENT EVALUATION DETAILS:")
student_period = EvaluationPeriod.objects.filter(
    evaluation_type='student',
    is_active=True
).first()
if student_period:
    print(f"  ✅ Active Period Found: {student_period.name}")
    print(f"     ID: {student_period.id}")
    print(f"     Is Active: {student_period.is_active}")
    print(f"     Start: {student_period.start_date}")
    print(f"     End: {student_period.end_date}")
else:
    print("  ❌ No active student period found")

# Check peer evaluation status
print("\n👥 PEER EVALUATION DETAILS:")
peer_period = EvaluationPeriod.objects.filter(
    evaluation_type='peer',
    is_active=True
).first()
if peer_period:
    print(f"  ✅ Active Period Found: {peer_period.name}")
    print(f"     ID: {peer_period.id}")
    print(f"     Is Active: {peer_period.is_active}")
    print(f"     Start: {peer_period.start_date}")
    print(f"     End: {peer_period.end_date}")
else:
    print("  ❌ No active peer period found")

# Check Evaluation model release status
print("\n📋 EVALUATION RELEASE STATUS:")
student_eval_released = Evaluation.objects.filter(evaluation_type='student', is_released=True).exists()
peer_eval_released = Evaluation.objects.filter(evaluation_type='peer', is_released=True).exists()
print(f"  Student Evaluation is_released: {student_eval_released}")
print(f"  Peer Evaluation is_released: {peer_eval_released}")

print("\n" + "=" * 80)
