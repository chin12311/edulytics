#!/usr/bin/env python
"""
COMPREHENSIVE DIAGNOSTIC SCRIPT
Checks all critical components of the peer evaluation system
"""

import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
sys.path.insert(0, 'c:\\Users\\ADMIN\\eval\\evaluation')

django.setup()

from main.models import User, UserProfile, Evaluation, EvaluationPeriod, EvaluationResponse, Role
from django.utils import timezone
from datetime import timedelta

print("\n" + "="*80)
print("COMPREHENSIVE PEER EVALUATION DIAGNOSTIC")
print("="*80 + "\n")

# ============================================================================
# CHECK 1: Database Connection
# ============================================================================
print("✓ CHECK 1: Database Connection")
print("-" * 80)
try:
    user_count = User.objects.count()
    print(f"✅ Database connected - {user_count} users found")
except Exception as e:
    print(f"❌ Database connection failed: {e}")
    sys.exit(1)

# ============================================================================
# CHECK 2: User Roles
# ============================================================================
print("\n✓ CHECK 2: User Roles Distribution")
print("-" * 80)
roles_count = {}
for role in Role:
    count = UserProfile.objects.filter(role=role).count()
    roles_count[role] = count
    print(f"   {role}: {count} users")

total_users = sum(roles_count.values())
print(f"\n   Total staff members (Faculty/Dean/Coordinator): {roles_count.get(Role.FACULTY, 0) + roles_count.get(Role.DEAN, 0) + roles_count.get(Role.COORDINATOR, 0)}")
print(f"   Total students: {roles_count.get(Role.STUDENT, 0)}")

# ============================================================================
# CHECK 3: Evaluation Periods
# ============================================================================
print("\n✓ CHECK 3: Evaluation Periods")
print("-" * 80)

print("\n📍 PEER PERIODS:")
peer_periods = EvaluationPeriod.objects.filter(evaluation_type='peer').order_by('-created_at')[:5]
if peer_periods.exists():
    for period in peer_periods:
        print(f"   ID: {period.id} | Name: {period.name}")
        print(f"      Type: {period.evaluation_type}")
        print(f"      Active: {period.is_active}")
        print(f"      Start: {period.start_date} | End: {period.end_date}")
        print(f"      Created: {period.created_at}")
    
    # Check for active peer period
    active_peer = EvaluationPeriod.objects.filter(evaluation_type='peer', is_active=True).first()
    if active_peer:
        print(f"\n   ✅ FOUND ACTIVE PEER PERIOD: ID={active_peer.id}, Name='{active_peer.name}'")
    else:
        print(f"\n   ❌ NO ACTIVE PEER PERIOD FOUND")
else:
    print("   ❌ NO PEER PERIODS AT ALL")

print("\n📍 STUDENT PERIODS:")
student_periods = EvaluationPeriod.objects.filter(evaluation_type='student').order_by('-created_at')[:5]
if student_periods.exists():
    for period in student_periods:
        print(f"   ID: {period.id} | Name: {period.name}")
        print(f"      Type: {period.evaluation_type}")
        print(f"      Active: {period.is_active}")
        print(f"      Start: {period.start_date} | End: {period.end_date}")
    
    active_student = EvaluationPeriod.objects.filter(evaluation_type='student', is_active=True).first()
    if active_student:
        print(f"\n   ✅ FOUND ACTIVE STUDENT PERIOD: ID={active_student.id}, Name='{active_student.name}'")
    else:
        print(f"\n   ❌ NO ACTIVE STUDENT PERIOD FOUND")
else:
    print("   ❌ NO STUDENT PERIODS AT ALL")

# ============================================================================
# CHECK 4: Evaluation Records
# ============================================================================
print("\n✓ CHECK 4: Evaluation Records")
print("-" * 80)

print("\n📍 PEER EVALUATIONS:")
peer_evals = Evaluation.objects.filter(evaluation_type='peer').order_by('-created_at')[:5]
if peer_evals.exists():
    for eval_obj in peer_evals:
        period_id = eval_obj.evaluation_period_id if eval_obj.evaluation_period else "NULL"
        print(f"   ID: {eval_obj.id}")
        print(f"      Type: {eval_obj.evaluation_type}")
        print(f"      Released: {eval_obj.is_released}")
        print(f"      Period ID: {period_id}")
        print(f"      Created: {eval_obj.created_at}")
    
    # Check for released peer evaluation
    released_peer = Evaluation.objects.filter(evaluation_type='peer', is_released=True).first()
    if released_peer:
        print(f"\n   ✅ FOUND RELEASED PEER EVALUATION: ID={released_peer.id}")
        if released_peer.evaluation_period:
            print(f"      Linked to period: {released_peer.evaluation_period.id} ({released_peer.evaluation_period.name})")
            print(f"      Period is active: {released_peer.evaluation_period.is_active}")
        else:
            print(f"      ⚠️  NO PERIOD LINKED (NULL)")
    else:
        print(f"\n   ❌ NO RELEASED PEER EVALUATION FOUND")
else:
    print("   ❌ NO PEER EVALUATIONS AT ALL")

print("\n📍 STUDENT EVALUATIONS:")
student_evals = Evaluation.objects.filter(evaluation_type='student').order_by('-created_at')[:5]
if student_evals.exists():
    for eval_obj in student_evals:
        period_id = eval_obj.evaluation_period_id if eval_obj.evaluation_period else "NULL"
        print(f"   ID: {eval_obj.id}")
        print(f"      Type: {eval_obj.evaluation_type}")
        print(f"      Released: {eval_obj.is_released}")
        print(f"      Period ID: {period_id}")
    
    released_student = Evaluation.objects.filter(evaluation_type='student', is_released=True).first()
    if released_student:
        print(f"\n   ✅ FOUND RELEASED STUDENT EVALUATION: ID={released_student.id}")
    else:
        print(f"\n   ❌ NO RELEASED STUDENT EVALUATION FOUND")
else:
    print("   ❌ NO STUDENT EVALUATIONS AT ALL")

# ============================================================================
# CHECK 5: Evaluation Responses (Submissions)
# ============================================================================
print("\n✓ CHECK 5: Evaluation Responses (Submissions)")
print("-" * 80)

total_responses = EvaluationResponse.objects.count()
print(f"   Total responses in database: {total_responses}")

peer_responses = EvaluationResponse.objects.filter(evaluation_period__evaluation_type='peer').count()
student_responses = EvaluationResponse.objects.count() - peer_responses
print(f"   Peer responses: {peer_responses}")
print(f"   Student responses: {student_responses}")

recent_peer_responses = EvaluationResponse.objects.filter(
    evaluation_period__evaluation_type='peer'
).order_by('-created_at')[:3]
if recent_peer_responses.exists():
    print("\n   Recent peer responses:")
    for response in recent_peer_responses:
        print(f"      Evaluator: {response.evaluator.username} ({response.evaluator.userprofile.role})")
        print(f"      Evaluatee: {response.evaluatee.username} ({response.evaluatee.userprofile.role})")
        print(f"      Period: {response.evaluation_period.name}")
        print(f"      Created: {response.created_at}")

# ============================================================================
# CHECK 6: Release Functions Status
# ============================================================================
print("\n✓ CHECK 6: Critical Function Verification")
print("-" * 80)

from main.views import evaluation_form_staffs, EvaluationView

print("   ✅ evaluation_form_staffs() function: EXISTS")
print("   ✅ EvaluationView class: EXISTS")

# Check if the functions have the new logic
import inspect
form_source = inspect.getsource(evaluation_form_staffs)
view_source = inspect.getsource(EvaluationView.get)

if "AUTO-CREATE" in form_source:
    print("   ✅ evaluation_form_staffs() has AUTO-CREATE fallback")
else:
    print("   ❌ evaluation_form_staffs() missing AUTO-CREATE fallback")

if "evaluation_type='peer'" in view_source:
    print("   ✅ EvaluationView checks for peer evaluation type")
else:
    print("   ❌ EvaluationView does NOT check evaluation type")

# ============================================================================
# CHECK 7: URLs Configuration
# ============================================================================
print("\n✓ CHECK 7: URL Configuration")
print("-" * 80)

print("   evaluationform_staffs URL: main:evaluationform_staffs")
print("   evaluation URL: main:evaluation")

# ============================================================================
# CHECK 8: Template Rendering
# ============================================================================
print("\n✓ CHECK 8: Template Status")
print("-" * 80)

import os
template_dir = 'c:\\Users\\ADMIN\\eval\\evaluation\\main\\templates\\main'
templates = {
    'evaluation.html': 'Evaluation overview page',
    'evaluationform_staffs.html': 'Staff peer evaluation form',
    'no_active_evaluation.html': 'Error page when no evaluation available',
}

for template_file, description in templates.items():
    path = os.path.join(template_dir, template_file)
    if os.path.exists(path):
        print(f"   ✅ {template_file}: EXISTS ({description})")
    else:
        print(f"   ❌ {template_file}: MISSING ({description})")

# ============================================================================
# SUMMARY
# ============================================================================
print("\n" + "="*80)
print("DIAGNOSTIC SUMMARY")
print("="*80 + "\n")

issues = []

# Check for active peer period
if not EvaluationPeriod.objects.filter(evaluation_type='peer', is_active=True).exists():
    issues.append("❌ NO ACTIVE PEER EVALUATION PERIOD")

# Check for released peer evaluation
released_peer = Evaluation.objects.filter(evaluation_type='peer', is_released=True).first()
if not released_peer:
    issues.append("❌ NO RELEASED PEER EVALUATION")
elif not released_peer.evaluation_period:
    issues.append(f"❌ RELEASED PEER EVALUATION (ID={released_peer.id}) HAS NO LINKED PERIOD")

# Check if staff can be assigned
staff_count = UserProfile.objects.filter(role__in=[Role.FACULTY, Role.DEAN, Role.COORDINATOR]).count()
if staff_count < 2:
    issues.append(f"❌ INSUFFICIENT STAFF MEMBERS ({staff_count}) - Need at least 2 to evaluate each other")

if issues:
    print("ISSUES FOUND:")
    for issue in issues:
        print(f"  {issue}")
else:
    print("✅ ALL CHECKS PASSED - System is ready!")

print("\n" + "="*80)
