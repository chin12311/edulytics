#!/usr/bin/env python
"""
Debug script to check why results aren't displaying
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'evaluationWeb.settings')
django.setup()

from django.contrib.auth.models import User
from main.models import EvaluationResponse, EvaluationResult, EvaluationPeriod, Section
from django.utils import timezone

print("="*70)
print("DEBUGGING RESULTS DISPLAY ISSUE")
print("="*70)

# Check evaluation periods
print("\n📅 EVALUATION PERIODS:")
periods = EvaluationPeriod.objects.filter(evaluation_type='student').order_by('-end_date')
for p in periods[:5]:
    status = "ACTIVE" if p.is_active else "INACTIVE"
    is_past = "PAST" if p.end_date <= timezone.now() else "FUTURE"
    print(f"\n{status} ({is_past}): {p.name}")
    print(f"  ID: {p.id}")
    print(f"  Start: {p.start_date}")
    print(f"  End: {p.end_date}")
    print(f"  Now: {timezone.now()}")
    
    # Check responses in this period
    responses = EvaluationResponse.objects.filter(evaluation_period=p)
    print(f"  Responses: {responses.count()}")
    
    # Check results in this period
    results = EvaluationResult.objects.filter(evaluation_period=p)
    print(f"  Results: {results.count()}")
    
    if responses.count() > 0:
        print(f"  ⚠️ {responses.count()} responses exist but {results.count()} results")

# Check which period would be selected by the query
print("\n" + "="*70)
print("PERIOD SELECTION QUERY TEST:")
print("="*70)

latest_completed = EvaluationPeriod.objects.filter(
    evaluation_type='student',
    is_active=False,
    end_date__lte=timezone.now()
).order_by('-end_date').first()

if latest_completed:
    print(f"\n✅ Latest completed period: {latest_completed.name}")
    print(f"   End date: {latest_completed.end_date}")
    print(f"   Responses: {EvaluationResponse.objects.filter(evaluation_period=latest_completed).count()}")
    print(f"   Results: {EvaluationResult.objects.filter(evaluation_period=latest_completed).count()}")
    
    if EvaluationResponse.objects.filter(evaluation_period=latest_completed).exists():
        print("\n   ⚠️ WARNING: Responses exist but may not have been processed to EvaluationResult!")
        print("   Action needed: Click 'Unrelease Student Evaluation' button to process results")
else:
    print("\n❌ No completed period found!")
    print("   This means either:")
    print("   1. No evaluation periods exist")
    print("   2. All periods are still active (is_active=True)")
    print("   3. All inactive periods have future end dates")

# Check for responses without a period
print("\n" + "="*70)
print("ORPHANED RESPONSES CHECK:")
print("="*70)

orphaned = EvaluationResponse.objects.filter(evaluation_period__isnull=True)
print(f"\nResponses without period: {orphaned.count()}")

if orphaned.count() > 0:
    print("   ⚠️ These responses won't appear in results!")
    print("   Sample orphaned responses:")
    for r in orphaned[:5]:
        print(f"   - {r.evaluator.username} → {r.evaluatee.username} (Section: {r.student_section})")

# Check sections with responses vs results
print("\n" + "="*70)
print("SECTION RESPONSE vs RESULT COMPARISON:")
print("="*70)

sections_with_responses = EvaluationResponse.objects.values_list('student_section', flat=True).distinct()
print(f"\nSections with responses: {list(sections_with_responses)}")

if latest_completed:
    sections_with_results = EvaluationResult.objects.filter(
        evaluation_period=latest_completed
    ).values_list('section__code', flat=True).distinct()
    print(f"Sections with results (in latest period): {list(sections_with_results)}")
    
    missing = set(sections_with_responses) - set(sections_with_results)
    if missing:
        print(f"\n⚠️ Sections with responses but NO results: {list(missing)}")
        print("   These won't display in profile settings!")

# Check a specific user's data
print("\n" + "="*70)
print("SAMPLE USER CHECK:")
print("="*70)

# Get first user with responses
sample_response = EvaluationResponse.objects.first()
if sample_response:
    user = sample_response.evaluatee
    print(f"\nChecking user: {user.username}")
    
    # Check their responses
    user_responses = EvaluationResponse.objects.filter(evaluatee=user)
    print(f"Total responses: {user_responses.count()}")
    
    # Check their results
    user_results = EvaluationResult.objects.filter(user=user)
    print(f"Total results: {user_results.count()}")
    
    if latest_completed:
        period_responses = user_responses.filter(evaluation_period=latest_completed)
        period_results = user_results.filter(evaluation_period=latest_completed)
        print(f"\nIn latest completed period:")
        print(f"  Responses: {period_responses.count()}")
        print(f"  Results: {period_results.count()}")
        
        if period_responses.count() > 0 and period_results.count() == 0:
            print(f"\n  ❌ ISSUE FOUND: User has {period_responses.count()} responses but 0 results!")
            print(f"  Solution: Admin needs to click 'Unrelease Student Evaluation' to process results")

print("\n" + "="*70)
print("SUMMARY & RECOMMENDATIONS:")
print("="*70)

total_responses = EvaluationResponse.objects.count()
total_results = EvaluationResult.objects.count()

print(f"\n📊 System totals:")
print(f"   Total responses: {total_responses}")
print(f"   Total results: {total_results}")

if total_responses > total_results:
    print(f"\n⚠️ GAP DETECTED: {total_responses - total_results} responses not processed!")
    print(f"\n💡 SOLUTION:")
    print(f"   1. Go to Admin panel")
    print(f"   2. Click 'Unrelease Student Evaluation' button")
    print(f"   3. This will process all responses into EvaluationResult table")
    print(f"   4. Results will then appear in profile settings")

if latest_completed is None:
    print(f"\n⚠️ NO COMPLETED PERIOD:")
    print(f"   The system is looking for inactive periods with end_date <= now")
    print(f"   Make sure to click 'Unrelease' to end the evaluation period")

print("\n" + "="*70)
