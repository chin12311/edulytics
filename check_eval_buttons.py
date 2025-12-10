from main.models import Evaluation, EvaluationPeriod

print("=" * 60)
print("EVALUATION STATUS CHECK")
print("=" * 60)

student_released = Evaluation.objects.filter(evaluation_type='student', is_released=True).count()
peer_released = Evaluation.objects.filter(evaluation_type='peer', is_released=True).count()

student_period = EvaluationPeriod.objects.filter(evaluation_type='student', is_active=True).exists()
peer_period = EvaluationPeriod.objects.filter(evaluation_type='peer', is_active=True).exists()

print(f"\nStudent Evaluation:")
print(f"  Released: {student_released}")
print(f"  Active Period: {'Yes' if student_period else 'No'}")

print(f"\nPeer Evaluation:")
print(f"  Released: {peer_released}")
print(f"  Active Period: {'Yes' if peer_period else 'No'}")

if student_period:
    sp = EvaluationPeriod.objects.filter(evaluation_type='student', is_active=True).first()
    print(f"\n  Student Period: {sp.name}")
    
if peer_period:
    pp = EvaluationPeriod.objects.filter(evaluation_type='peer', is_active=True).first()
    print(f"  Peer Period: {pp.name}")

print("\n" + "=" * 60)
