#!/usr/bin/env python
"""
Fix peer evaluation linkage issues - ensure all released peer evaluations are linked to active period
"""
import os
import sys
import django

# Setup Django
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'evaluation.settings')
django.setup()

from django.utils import timezone
from main.models import Evaluation, EvaluationPeriod, Role

print("=" * 100)
print("PEER EVALUATION LINKAGE FIX")
print("=" * 100)

# STEP 1: Check current state
print("\n1️⃣ CHECKING CURRENT STATE:")
print("-" * 100)

active_peer_periods = EvaluationPeriod.objects.filter(evaluation_type='peer', is_active=True)
print(f"Active peer periods: {active_peer_periods.count()}")
for period in active_peer_periods:
    print(f"   ✅ {period.id}: {period.name} (Active={period.is_active})")

released_peer_evals = Evaluation.objects.filter(evaluation_type='peer', is_released=True)
print(f"\nReleased peer evaluations: {released_peer_evals.count()}")
for eval_rec in released_peer_evals:
    period_status = f"Period={eval_rec.evaluation_period_id}" if eval_rec.evaluation_period_id else "Period=NULL ❌"
    print(f"   ID={eval_rec.id}: {period_status}")

# STEP 2: Fix orphaned released evaluations
print("\n2️⃣ FIXING ORPHANED RELEASED EVALUATIONS:")
print("-" * 100)

# Get released evaluations with NULL period
orphaned_evals = Evaluation.objects.filter(
    evaluation_type='peer',
    is_released=True,
    evaluation_period__isnull=True
)

if orphaned_evals.exists():
    print(f"Found {orphaned_evals.count()} orphaned released peer evaluation(s)")
    
    # Get the active period (or create one if needed)
    active_period, created = EvaluationPeriod.objects.get_or_create(
        evaluation_type='peer',
        is_active=True,
        defaults={
            'name': f"Peer Evaluation {timezone.now().strftime('%B %Y')}",
            'start_date': timezone.now(),
            'end_date': timezone.now() + timezone.timedelta(days=30),
        }
    )
    
    if created:
        print(f"   📝 Created new active peer period: {active_period.id}")
    else:
        print(f"   ✅ Using existing active period: {active_period.id}")
    
    # Link orphaned evaluations to active period
    updated = orphaned_evals.update(evaluation_period=active_period)
    print(f"   ✅ Linked {updated} orphaned evaluation(s) to active period")
else:
    print("✅ No orphaned evaluations found")

# STEP 3: Check for multiple active periods (should only have one)
print("\n3️⃣ CHECKING FOR MULTIPLE ACTIVE PEER PERIODS:")
print("-" * 100)

multiple_active = EvaluationPeriod.objects.filter(evaluation_type='peer', is_active=True)
if multiple_active.count() > 1:
    print(f"⚠️  Found {multiple_active.count()} active peer periods - consolidating...")
    
    periods_list = list(multiple_active.order_by('-created_at'))
    main_period = periods_list[0]
    periods_to_deactivate = periods_list[1:]
    
    # Deactivate extras and link their evaluations to main period
    for old_period in periods_to_deactivate:
        old_period.is_active = False
        old_period.save()
        
        # Link any evaluations from this period to main period
        Evaluation.objects.filter(
            evaluation_type='peer',
            evaluation_period=old_period
        ).update(evaluation_period=main_period)
        
        print(f"   ✅ Deactivated period {old_period.id}, linked evaluations to {main_period.id}")
else:
    print(f"✅ Correct number of active periods: {multiple_active.count()}")

# STEP 4: Verify all released peer evaluations are linked
print("\n4️⃣ VERIFYING ALL RELEASED PEER EVALUATIONS:")
print("-" * 100)

released_peer_evals = Evaluation.objects.filter(evaluation_type='peer', is_released=True)
orphaned_after_fix = released_peer_evals.filter(evaluation_period__isnull=True)

if not orphaned_after_fix.exists():
    print(f"✅ All {released_peer_evals.count()} released peer evaluations are linked to a period")
    for eval_rec in released_peer_evals:
        print(f"   ✅ ID={eval_rec.id} -> Period={eval_rec.evaluation_period.name} (Active={eval_rec.evaluation_period.is_active})")
else:
    print(f"❌ Found {orphaned_after_fix.count()} orphaned released evaluations after fix!")
    for eval_rec in orphaned_after_fix:
        print(f"   ❌ ID={eval_rec.id}")

# STEP 5: Final status
print("\n5️⃣ FINAL STATUS:")
print("-" * 100)

active_period = EvaluationPeriod.objects.filter(evaluation_type='peer', is_active=True).first()
if active_period:
    released_linked = Evaluation.objects.filter(
        evaluation_type='peer',
        is_released=True,
        evaluation_period=active_period
    ).exists()
    
    print(f"✅ Active peer period: {active_period.name}")
    print(f"✅ Released peer evaluation linked: {released_linked}")
    
    if released_linked:
        print("\n✅ READY! Dean should now be able to access peer evaluation form")
    else:
        print("\n❌ Released evaluation not linked to active period - needs manual investigation")
else:
    print("❌ No active peer evaluation period found - nothing to link to")

print("\n" + "=" * 100)
