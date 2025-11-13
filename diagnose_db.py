"""
Quick diagnostic - check what's actually in the database
Run from Django shell: python manage.py shell < diagnose_db.py
"""

from main.models import EvaluationPeriod, Evaluation, Role, UserProfile, User
from django.utils import timezone

print("\n" + "="*80)
print("DATABASE DIAGNOSTIC - PEER EVALUATION")
print("="*80)

# 1. Check all peer periods
print("\n1. ALL PEER EVALUATION PERIODS:")
all_periods = EvaluationPeriod.objects.filter(evaluation_type='peer').order_by('-created_at')
print(f"   Total: {all_periods.count()}")
for p in all_periods[:5]:
    print(f"   - ID={p.id}, Name={p.name}, Active={p.is_active}, Created={p.created_at}")

# 2. Check active peer period
print("\n2. ACTIVE PEER PERIODS:")
active_periods = EvaluationPeriod.objects.filter(evaluation_type='peer', is_active=True)
print(f"   Total: {active_periods.count()}")
for p in active_periods:
    print(f"   - ID={p.id}, Name={p.name}")

# 3. Check all peer evaluations
print("\n3. ALL PEER EVALUATIONS:")
all_evals = Evaluation.objects.filter(evaluation_type='peer').order_by('-created_at')
print(f"   Total: {all_evals.count()}")
for e in all_evals[:5]:
    period_info = f"Period={e.evaluation_period_id}" if e.evaluation_period_id else "Period=NULL"
    print(f"   - ID={e.id}, Released={e.is_released}, {period_info}, Created={e.created_at}")

# 4. Check released peer evaluations
print("\n4. RELEASED PEER EVALUATIONS:")
released = Evaluation.objects.filter(evaluation_type='peer', is_released=True)
print(f"   Total: {released.count()}")
for e in released:
    period_info = f"Period={e.evaluation_period_id}" if e.evaluation_period_id else "Period=NULL"
    print(f"   - ID={e.id}, {period_info}")
    if e.evaluation_period:
        print(f"      Linked to: {e.evaluation_period.name}, Active={e.evaluation_period.is_active}")

# 5. Check released evaluations linked to active period
print("\n5. RELEASED PEER EVALUATIONS LINKED TO ACTIVE PERIOD:")
if active_periods.exists():
    active = active_periods.first()
    linked = Evaluation.objects.filter(
        evaluation_type='peer',
        is_released=True,
        evaluation_period=active
    )
    print(f"   Active Period: {active.name} (ID={active.id})")
    print(f"   Linked Evals: {linked.count()}")
    for e in linked:
        print(f"   - ID={e.id}, Released={e.is_released}")
else:
    print("   NO ACTIVE PERIOD!")

# 6. Check student evaluation for comparison
print("\n6. STUDENT EVALUATION (for comparison):")
student_active = EvaluationPeriod.objects.filter(evaluation_type='student', is_active=True)
print(f"   Active student periods: {student_active.count()}")
student_released = Evaluation.objects.filter(evaluation_type='student', is_released=True)
print(f"   Released student evaluations: {student_released.count()}")

# 7. Check Dean user
print("\n7. DEAN USERS:")
deans = User.objects.filter(userprofile__role='DEAN')
print(f"   Total: {deans.count()}")
for dean in deans[:3]:
    print(f"   - {dean.username} (ID={dean.id}), Institute={dean.userprofile.institute}")

print("\n" + "="*80)
print("END DIAGNOSTIC")
print("="*80 + "\n")
