import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'evaluation.settings')
django.setup()

from main.models import Evaluation, EvaluationPeriod
from django.utils import timezone

print("=" * 80)
print("CURRENT EVALUATION STATUS")
print("=" * 80)

# Check Student Evaluation status
print("\n📚 STUDENT EVALUATION:")
student_evals = Evaluation.objects.filter(evaluation_type='student')
print(f"   Total student evaluations: {student_evals.count()}")
released_student = student_evals.filter(is_released=True)
print(f"   Released: {released_student.count()}")
print(f"   Unreleased: {student_evals.filter(is_released=False).count()}")

student_period = EvaluationPeriod.objects.filter(
    evaluation_type='student',
    is_active=True
).first()

if student_period:
    print(f"   ✅ Active Period: {student_period.name}")
    print(f"   Start: {student_period.start_date.strftime('%B %d, %Y %H:%M')}")
    print(f"   End: {student_period.end_date.strftime('%B %d, %Y %H:%M')}")
else:
    print(f"   ❌ No active period")

# Check Peer Evaluation status
print("\n👥 PEER EVALUATION:")
peer_evals = Evaluation.objects.filter(evaluation_type='peer')
print(f"   Total peer evaluations: {peer_evals.count()}")
released_peer = peer_evals.filter(is_released=True)
print(f"   Released: {released_peer.count()}")
print(f"   Unreleased: {peer_evals.filter(is_released=False).count()}")

peer_period = EvaluationPeriod.objects.filter(
    evaluation_type='peer',
    is_active=True
).first()

if peer_period:
    print(f"   ✅ Active Period: {peer_period.name}")
    print(f"   Start: {peer_period.start_date.strftime('%B %d, %Y %H:%M')}")
    print(f"   End: {peer_period.end_date.strftime('%B %d, %Y %H:%M')}")
else:
    print(f"   ❌ No active period")

print("\n" + "=" * 80)
print("SUMMARY")
print("=" * 80)
print(f"Student Evaluation: {'🟢 ACTIVE' if student_period else '🔴 INACTIVE'}")
print(f"Peer Evaluation: {'🟢 ACTIVE' if peer_period else '🔴 INACTIVE'}")
print("=" * 80)
