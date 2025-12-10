from main.models import Evaluation, EvaluationPeriod

print("=" * 80)
print("EVALUATION RECORDS STATUS")
print("=" * 80)

# Check Evaluation table
print("\n📋 EVALUATION RECORDS:")
student_evals = Evaluation.objects.filter(evaluation_type='student')
print(f"Total student evaluation records: {student_evals.count()}")
for eval in student_evals:
    print(f"  ID: {eval.id} | Released: {eval.is_released} | Period: {eval.evaluation_period}")

peer_evals = Evaluation.objects.filter(evaluation_type='peer')
print(f"\nTotal peer evaluation records: {peer_evals.count()}")
for eval in peer_evals:
    print(f"  ID: {eval.id} | Released: {eval.is_released} | Period: {eval.evaluation_period}")

# Check active periods
print("\n📅 ACTIVE PERIODS:")
active_student = EvaluationPeriod.objects.filter(evaluation_type='student', is_active=True).first()
if active_student:
    print(f"Student: {active_student.name} (ID: {active_student.id})")
else:
    print("Student: None")

active_peer = EvaluationPeriod.objects.filter(evaluation_type='peer', is_active=True).first()
if active_peer:
    print(f"Peer: {active_peer.name} (ID: {active_peer.id})")
else:
    print("Peer: None")

print("=" * 80)
