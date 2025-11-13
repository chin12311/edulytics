#!/usr/bin/env python
"""
Comprehensive diagnostic script for peer evaluation issues.
"""
import os
import django
import sys

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'evaluation.settings')
django.setup()

from main.models import EvaluationPeriod, Evaluation, EvaluationResponse, User, UserProfile

print("=" * 80)
print("PEER EVALUATION DIAGNOSTIC REPORT")
print("=" * 80)

# 1. Check for active peer evaluation periods
print("\n1️⃣ CHECKING PEER EVALUATION PERIODS:")
print("-" * 80)
peer_periods = EvaluationPeriod.objects.filter(evaluation_type='peer').order_by('-created_at')
if peer_periods.exists():
    for period in peer_periods[:5]:  # Show last 5
        print(f"   ID: {period.id}")
        print(f"   Name: {period.name}")
        print(f"   Type: {period.evaluation_type}")
        print(f"   Is Active: {period.is_active}")
        print(f"   Start Date: {period.start_date}")
        print(f"   End Date: {period.end_date}")
        print(f"   Created: {period.created_at}")
        print(f"   Updated: {period.updated_at}")
        print()
else:
    print("   ❌ NO PEER EVALUATION PERIODS FOUND!")

# 2. Check for released peer evaluation records
print("\n2️⃣ CHECKING PEER EVALUATION RECORDS (Released):")
print("-" * 80)
released_evaluations = Evaluation.objects.filter(
    evaluation_type='peer',
    is_released=True
).order_by('-created_at')

if released_evaluations.exists():
    for eval_rec in released_evaluations[:5]:  # Show last 5
        print(f"   ID: {eval_rec.id}")
        print(f"   Type: {eval_rec.evaluation_type}")
        print(f"   Is Released: {eval_rec.is_released}")
        print(f"   Evaluation Period ID: {eval_rec.evaluation_period_id}")
        if eval_rec.evaluation_period:
            print(f"   Period Name: {eval_rec.evaluation_period.name}")
            print(f"   Period Active: {eval_rec.evaluation_period.is_active}")
        print(f"   Created: {eval_rec.created_at}")
        print(f"   Updated: {eval_rec.updated_at}")
        print()
else:
    print("   ❌ NO RELEASED PEER EVALUATION RECORDS FOUND!")

# 3. Check for unreleased peer evaluation records
print("\n3️⃣ CHECKING PEER EVALUATION RECORDS (Unreleased):")
print("-" * 80)
unreleased_evaluations = Evaluation.objects.filter(
    evaluation_type='peer',
    is_released=False
).order_by('-created_at')

if unreleased_evaluations.exists():
    for eval_rec in unreleased_evaluations[:5]:
        print(f"   ID: {eval_rec.id}")
        print(f"   Type: {eval_rec.evaluation_type}")
        print(f"   Is Released: {eval_rec.is_released}")
        print(f"   Evaluation Period ID: {eval_rec.evaluation_period_id}")
        if eval_rec.evaluation_period:
            print(f"   Period Name: {eval_rec.evaluation_period.name}")
        print(f"   Created: {eval_rec.created_at}")
        print()
else:
    print("   ℹ️  No unreleased peer evaluation records.")

# 4. Check active student evaluation for comparison
print("\n4️⃣ CHECKING STUDENT EVALUATION (For Comparison):")
print("-" * 80)
student_eval = Evaluation.objects.filter(
    evaluation_type='student',
    is_released=True
).order_by('-created_at').first()

if student_eval:
    print(f"   ✅ FOUND Student Evaluation Record:")
    print(f"   ID: {student_eval.id}")
    print(f"   Is Released: {student_eval.is_released}")
    print(f"   Period ID: {student_eval.evaluation_period_id}")
    if student_eval.evaluation_period:
        print(f"   Period Name: {student_eval.evaluation_period.name}")
        print(f"   Period Active: {student_eval.evaluation_period.is_active}")
else:
    print("   ❌ No released student evaluation record")

# 5. Check active evaluation periods (both types)
print("\n5️⃣ CHECKING ALL ACTIVE EVALUATION PERIODS:")
print("-" * 80)
active_periods = EvaluationPeriod.objects.filter(is_active=True).order_by('-created_at')
if active_periods.exists():
    for period in active_periods:
        print(f"   ✅ {period.evaluation_type.upper()}")
        print(f"      Name: {period.name}")
        print(f"      ID: {period.id}")
        print()
else:
    print("   ❌ NO ACTIVE PERIODS FOUND!")

# 6. Check total count of each type
print("\n6️⃣ EVALUATION RECORD COUNTS:")
print("-" * 80)
total_periods = EvaluationPeriod.objects.count()
active_periods_count = EvaluationPeriod.objects.filter(is_active=True).count()
peer_periods_count = EvaluationPeriod.objects.filter(evaluation_type='peer').count()
active_peer_periods = EvaluationPeriod.objects.filter(evaluation_type='peer', is_active=True).count()

print(f"   Total Evaluation Periods: {total_periods}")
print(f"   Active Periods: {active_periods_count}")
print(f"   Peer Periods: {peer_periods_count}")
print(f"   Active Peer Periods: {active_peer_periods}")

total_evaluations = Evaluation.objects.count()
peer_evaluations = Evaluation.objects.filter(evaluation_type='peer').count()
released_peer = Evaluation.objects.filter(evaluation_type='peer', is_released=True).count()

print(f"   Total Evaluation Records: {total_evaluations}")
print(f"   Peer Evaluation Records: {peer_evaluations}")
print(f"   Released Peer Records: {released_peer}")

# 7. Check if Dean exists
print("\n7️⃣ CHECKING DEAN ACCOUNT:")
print("-" * 80)
try:
    deans = User.objects.filter(userprofile__role='DEAN')
    if deans.exists():
        for dean in deans:
            print(f"   ✅ Dean found: {dean.username} ({dean.get_full_name()})")
            print(f"      Institute: {dean.userprofile.institute}")
    else:
        print("   ❌ No Dean accounts found!")
except Exception as e:
    print(f"   ⚠️ Error checking deans: {e}")

print("\n" + "=" * 80)
print("END OF DIAGNOSTIC REPORT")
print("=" * 80)
