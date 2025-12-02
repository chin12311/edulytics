#!/usr/bin/env python
"""
Manually process evaluation responses to results for past periods
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'evaluationWeb.settings')
django.setup()

from django.utils import timezone
from main.models import EvaluationPeriod, EvaluationResponse, EvaluationResult
from main.views import process_evaluation_period_to_results

print("="*70)
print("MANUAL EVALUATION PROCESSING")
print("="*70)

# Find periods with responses but no results
periods_to_process = []

all_periods = EvaluationPeriod.objects.filter(evaluation_type='student', is_active=False)
for period in all_periods:
    response_count = EvaluationResponse.objects.filter(evaluation_period=period).count()
    result_count = EvaluationResult.objects.filter(evaluation_period=period).count()
    
    if response_count > 0 and result_count == 0:
        periods_to_process.append(period)
        print(f"\n⚠️ Found period with unprocessed responses:")
        print(f"   Period: {period.name} (ID: {period.id})")
        print(f"   Responses: {response_count}")
        print(f"   Results: {result_count}")

if not periods_to_process:
    print("\n✅ No unprocessed periods found!")
    print("   All inactive periods have been processed.")
else:
    print(f"\n\n{'='*70}")
    print(f"PROCESSING {len(periods_to_process)} PERIOD(S)...")
    print("="*70)
    
    for period in periods_to_process:
        print(f"\n📊 Processing: {period.name}")
        try:
            # Call the processing function
            process_evaluation_period_to_results(period)
            
            # Check results
            new_results = EvaluationResult.objects.filter(evaluation_period=period).count()
            print(f"   ✅ Created {new_results} results")
            
        except Exception as e:
            print(f"   ❌ Error: {e}")
            import traceback
            traceback.print_exc()

print("\n" + "="*70)
print("PROCESSING COMPLETE!")
print("="*70)

# Show summary
total_responses = EvaluationResponse.objects.count()
total_results = EvaluationResult.objects.count()
print(f"\n📊 Final system totals:")
print(f"   Total responses: {total_responses}")
print(f"   Total results: {total_results}")

if total_responses > total_results:
    print(f"\n⚠️ Still {total_responses - total_results} unprocessed responses")
    print(f"   These are likely in ACTIVE periods")
    print(f"   Click 'Unrelease' button to process them")
else:
    print(f"\n✅ All responses have been processed!")
