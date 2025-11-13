#!/usr/bin/env python
"""
CRITICAL FIX SCRIPT
Repairs the broken evaluation system
"""

import os
import sys
import django
from datetime import timedelta

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
sys.path.insert(0, 'c:\\Users\\ADMIN\\eval\\evaluation')

django.setup()

from main.models import EvaluationPeriod, Evaluation, Role, UserProfile
from django.utils import timezone

print("\n" + "="*80)
print("CRITICAL DATABASE REPAIR")
print("="*80 + "\n")

# PROBLEM 1: No active period
print("STEP 1: Checking for active peer period...")
active_peer_period = EvaluationPeriod.objects.filter(evaluation_type='peer', is_active=True).first()

if not active_peer_period:
    print("❌ No active peer period found - CREATING ONE NOW")
    
    # Deactivate all other peer periods first
    EvaluationPeriod.objects.filter(evaluation_type='peer', is_active=True).update(is_active=False)
    
    # Create new active period
    active_peer_period = EvaluationPeriod.objects.create(
        name=f"Peer Evaluation {timezone.now().strftime('%B %Y')}",
        evaluation_type='peer',
        start_date=timezone.now(),
        end_date=timezone.now() + timedelta(days=30),
        is_active=True
    )
    print(f"✅ Created active peer period: ID={active_peer_period.id}, Name='{active_peer_period.name}'")
else:
    print(f"✅ Active peer period found: ID={active_peer_period.id}, Name='{active_peer_period.name}'")

# PROBLEM 2: Orphaned released evaluation
print("\nSTEP 2: Checking for released peer evaluation...")
orphaned_evals = Evaluation.objects.filter(
    evaluation_type='peer',
    is_released=True,
    evaluation_period__isnull=True
)

if orphaned_evals.exists():
    print(f"❌ Found {orphaned_evals.count()} orphaned released evaluations")
    for eval_obj in orphaned_evals:
        print(f"   Linking evaluation ID={eval_obj.id} to active period {active_peer_period.id}")
        eval_obj.evaluation_period = active_peer_period
        eval_obj.save()
        print(f"   ✅ Updated evaluation ID={eval_obj.id}")
else:
    print("❌ No released peer evaluation found - CREATING ONE NOW")
    released_eval = Evaluation.objects.create(
        evaluation_type='peer',
        is_released=True,
        evaluation_period=active_peer_period
    )
    print(f"✅ Created released peer evaluation: ID={released_eval.id}")

# Verify
print("\nSTEP 3: Verification")
print("-" * 80)

active_period = EvaluationPeriod.objects.filter(evaluation_type='peer', is_active=True).first()
released_peer_eval = Evaluation.objects.filter(
    evaluation_type='peer',
    is_released=True,
    evaluation_period=active_period
).first()

if active_period:
    print(f"✅ Active peer period: ID={active_period.id}, Name='{active_period.name}'")
else:
    print(f"❌ NO active peer period")

if released_peer_eval:
    print(f"✅ Released peer evaluation: ID={released_peer_eval.id}, linked to period {released_peer_eval.evaluation_period_id}")
else:
    print(f"❌ NO released peer evaluation")

# Check staff
staff_count = UserProfile.objects.filter(role__in=[Role.FACULTY, Role.DEAN, Role.COORDINATOR]).count()
print(f"✅ Staff members available: {staff_count}")

print("\n" + "="*80)
print("DATABASE REPAIR COMPLETE")
print("="*80 + "\n")
