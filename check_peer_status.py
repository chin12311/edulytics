#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'edulytics.settings')
django.setup()

from main.models import Evaluation, EvaluationPeriod, EvaluationResponse

print("\n" + "="*70)
print("🔍 PEER EVALUATION STATUS DEBUG")
print("="*70)

print("\n1️⃣ EVALUATION PERIODS:")
print("-" * 70)
peer_periods = EvaluationPeriod.objects.filter(evaluation_type='peer').order_by('-created_at')
if peer_periods.exists():
    for period in peer_periods:
        print(f"   • {period.name}")
        print(f"     - ID: {period.id}")
        print(f"     - is_active: {period.is_active}")
        print(f"     - start_date: {period.start_date}")
        print(f"     - end_date: {period.end_date}")
        print(f"     - created_at: {period.created_at}")
        print()
else:
    print("   ❌ No peer evaluation periods found!")

print("\n2️⃣ ACTIVE PEER EVALUATION PERIODS:")
print("-" * 70)
active_periods = EvaluationPeriod.objects.filter(evaluation_type='peer', is_active=True)
if active_periods.exists():
    for period in active_periods:
        print(f"   ✅ {period.name} (ID: {period.id})")
else:
    print("   ❌ No ACTIVE peer evaluation periods found!")

print("\n3️⃣ EVALUATION RECORDS (Peer Type):")
print("-" * 70)
peer_evals = Evaluation.objects.filter(evaluation_type='peer').order_by('-created_at')
if peer_evals.exists():
    for eval_rec in peer_evals:
        print(f"   • Evaluation ID: {eval_rec.id}")
        print(f"     - is_released: {eval_rec.is_released}")
        print(f"     - evaluation_period: {eval_rec.evaluation_period}")
        print(f"     - created_at: {eval_rec.created_at}")
        print()
else:
    print("   ❌ No peer evaluation records found!")

print("\n4️⃣ STUDENT EVALUATION RECORDS:")
print("-" * 70)
student_evals = Evaluation.objects.filter(evaluation_type='student').order_by('-created_at')
if student_evals.exists():
    for eval_rec in student_evals:
        print(f"   • Evaluation ID: {eval_rec.id}")
        print(f"     - is_released: {eval_rec.is_released}")
        print(f"     - evaluation_period: {eval_rec.evaluation_period}")
        print(f"     - created_at: {eval_rec.created_at}")
        print()
else:
    print("   ❌ No student evaluation records found!")

print("\n5️⃣ SUMMARY:")
print("-" * 70)
active_peer_period = EvaluationPeriod.objects.filter(evaluation_type='peer', is_active=True).first()
if active_peer_period:
    print(f"✅ Active Peer Period EXISTS: {active_peer_period.name}")
    has_peer_eval = Evaluation.objects.filter(is_released=True, evaluation_type='peer').exists()
    print(f"   - Has released Peer Evaluation: {has_peer_eval}")
else:
    print("❌ NO Active Peer Period - THIS IS THE PROBLEM!")
    
print("\n" + "="*70 + "\n")
