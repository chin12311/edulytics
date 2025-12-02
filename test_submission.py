"""
Test evaluation submission flow to diagnose why evaluations aren't saving
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'evaluationWeb.settings')
django.setup()

from django.contrib.auth.models import User
from main.models import EvaluationPeriod, EvaluationResponse, IrregularEvaluation, UserProfile, Section
from django.utils import timezone

print("\n" + "=" * 80)
print("TESTING EVALUATION SUBMISSION FLOW")
print("=" * 80)

# Check the users mentioned by the user
test_users = [
    'zyrahmastelero',  # Irregular
    'anthonyplanos',   # C405
    'jadepuno'         # Dean/peer
]

print("\n1️⃣ CHECKING USER ACCOUNTS:")
print("-" * 80)
for username in test_users:
    try:
        user = User.objects.get(username=username)
        profile = UserProfile.objects.get(user=user)
        print(f"\n✅ Found: {username}")
        print(f"   Role: {profile.role}")
        print(f"   Is Irregular: {profile.is_irregular}")
        print(f"   Section: {profile.section.code if profile.section else 'No Section'}")
        print(f"   Institute: {profile.institute}")
    except User.DoesNotExist:
        print(f"\n❌ User not found: {username}")
    except UserProfile.DoesNotExist:
        print(f"\n❌ Profile not found for: {username}")

# Check active evaluation period
print("\n\n2️⃣ CHECKING ACTIVE EVALUATION PERIOD:")
print("-" * 80)
try:
    active_period = EvaluationPeriod.objects.get(is_active=True)
    print(f"✅ Active Period: {active_period.name}")
    print(f"   ID: {active_period.id}")
    print(f"   Start: {active_period.start_date}")
    print(f"   End: {active_period.end_date}")
    print(f"   Is Active: {active_period.is_active}")
except EvaluationPeriod.DoesNotExist:
    print("❌ No active evaluation period found!")
    active_period = None
except EvaluationPeriod.MultipleObjectsReturned:
    print("⚠️ Multiple active periods found!")
    active_periods = EvaluationPeriod.objects.filter(is_active=True)
    for period in active_periods:
        print(f"   - {period.name} (ID: {period.id})")

# Check for any recent evaluation submissions from these users
print("\n\n3️⃣ CHECKING RECENT EVALUATION SUBMISSIONS:")
print("-" * 80)

for username in test_users:
    try:
        user = User.objects.get(username=username)
        
        # Check EvaluationResponse
        responses = EvaluationResponse.objects.filter(evaluator=user).order_by('-submitted_at')
        if responses.exists():
            print(f"\n✅ {username} has {responses.count()} EvaluationResponse(s):")
            for resp in responses[:3]:  # Show last 3
                print(f"   - ID {resp.id}: {resp.evaluatee.username} in {resp.evaluation_period.name}")
                print(f"     Section: {resp.student_section}, Submitted: {resp.submitted_at}")
        else:
            print(f"\n⚠️ {username} has NO EvaluationResponse entries")
        
        # Check IrregularEvaluation
        irregular_evals = IrregularEvaluation.objects.filter(evaluator=user).order_by('-submitted_at')
        if irregular_evals.exists():
            print(f"\n✅ {username} has {irregular_evals.count()} IrregularEvaluation(s):")
            for eval in irregular_evals[:3]:  # Show last 3
                print(f"   - ID {eval.id}: {eval.evaluatee.username} in {eval.evaluation_period.name}")
                print(f"     Submitted: {eval.submitted_at}")
        else:
            print(f"\n⚠️ {username} has NO IrregularEvaluation entries")
            
    except User.DoesNotExist:
        print(f"\n❌ Cannot check submissions for {username} - user not found")

# Check potential evaluatees
print("\n\n4️⃣ CHECKING POTENTIAL EVALUATEES:")
print("-" * 80)
faculty_users = User.objects.filter(userprofile__role__in=['Faculty', 'Coordinator', 'Dean'])
print(f"Found {faculty_users.count()} faculty/coordinator/dean accounts:")
for user in faculty_users[:10]:  # Show first 10
    profile = user.userprofile
    print(f"   - {user.username} ({profile.role}, {profile.institute})")

# Summary
print("\n\n" + "=" * 80)
print("DIAGNOSIS SUMMARY")
print("=" * 80)

issues = []

# Check if users exist
for username in test_users:
    if not User.objects.filter(username=username).exists():
        issues.append(f"❌ User '{username}' does not exist in database")

# Check if active period exists
if not EvaluationPeriod.objects.filter(is_active=True).exists():
    issues.append("❌ No active evaluation period found")
elif EvaluationPeriod.objects.filter(is_active=True).count() > 1:
    issues.append("⚠️ Multiple active evaluation periods found")

# Check for submissions
for username in test_users:
    try:
        user = User.objects.get(username=username)
        if not EvaluationResponse.objects.filter(evaluator=user).exists() and \
           not IrregularEvaluation.objects.filter(evaluator=user).exists():
            issues.append(f"⚠️ User '{username}' has never submitted any evaluations")
    except User.DoesNotExist:
        pass

if issues:
    print("\n🔍 POTENTIAL ISSUES FOUND:")
    for issue in issues:
        print(f"   {issue}")
else:
    print("\n✅ No obvious issues found - submission flow should work")

print("\n" + "=" * 80)
