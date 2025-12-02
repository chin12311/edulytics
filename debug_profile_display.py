"""
Debug profile settings display - check what data is being shown
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'evaluationWeb.settings')
django.setup()

from main.models import EvaluationResult, User, EvaluationPeriod
from django.utils import timezone

print("\n" + "=" * 80)
print("PROFILE SETTINGS DATA CHECK")
print("=" * 80)

# Check Dean user (jadepuno based on earlier tests)
try:
    dean_user = User.objects.get(username='jadepuno')
    print(f"\n✅ Found Dean: {dean_user.username}")
    print(f"   Role: {dean_user.userprofile.role}")
    print(f"   Institute: {dean_user.userprofile.institute}")
except User.DoesNotExist:
    print("\n❌ Dean user 'jadepuno' not found")
    dean_user = None

if dean_user:
    # Check what periods exist
    print("\n📅 EVALUATION PERIODS:")
    print("-" * 80)
    all_periods = EvaluationPeriod.objects.all().order_by('-start_date')
    for period in all_periods:
        status = "ACTIVE" if period.is_active else "INACTIVE"
        completed = "COMPLETED" if period.end_date <= timezone.now() else "ONGOING"
        print(f"   - {period.name} ({period.evaluation_type})")
        print(f"     Status: {status}, {completed}")
        print(f"     ID: {period.id}, End: {period.end_date}")

    # Check latest completed period
    latest_completed = EvaluationPeriod.objects.filter(
        evaluation_type='student',
        is_active=False,
        end_date__lte=timezone.now()
    ).order_by('-end_date').first()
    
    if latest_completed:
        print(f"\n📊 LATEST COMPLETED PERIOD: {latest_completed.name} (ID: {latest_completed.id})")
    else:
        print(f"\n⚠️ NO COMPLETED PERIODS FOUND")

    # Check results for dean
    print(f"\n📈 EVALUATION RESULTS FOR {dean_user.username}:")
    print("-" * 80)
    
    # All results
    all_results = EvaluationResult.objects.filter(user=dean_user).order_by('-calculated_at')
    if all_results.exists():
        print(f"   Found {all_results.count()} result(s):")
        for result in all_results:
            section_name = result.section.code if result.section else "No Section"
            print(f"\n   Result ID {result.id}:")
            print(f"   - Period: {result.evaluation_period.name} (ID: {result.evaluation_period.id})")
            print(f"   - Section: {section_name}")
            print(f"   - Score: {result.total_percentage}%")
            print(f"   - Responses: {result.total_responses}")
            print(f"   - Period Active: {result.evaluation_period.is_active}")
            print(f"   - Period End: {result.evaluation_period.end_date}")
            print(f"   - Calculated: {result.calculated_at}")
    else:
        print("   ❌ No results found")

    # Check results by period type
    print(f"\n📋 RESULTS BY PERIOD TYPE:")
    print("-" * 80)
    
    # Latest completed student period results
    if latest_completed:
        completed_results = EvaluationResult.objects.filter(
            user=dean_user,
            evaluation_period=latest_completed
        )
        print(f"   Latest Completed Period ({latest_completed.name}):")
        print(f"   - Results: {completed_results.count()}")
    
    # Active period results (shouldn't show but let's check)
    active_period = EvaluationPeriod.objects.filter(is_active=True).first()
    if active_period:
        active_results = EvaluationResult.objects.filter(
            user=dean_user,
            evaluation_period=active_period
        )
        print(f"   Active Period ({active_period.name}):")
        print(f"   - Results: {active_results.count()}")

print("\n" + "=" * 80)
