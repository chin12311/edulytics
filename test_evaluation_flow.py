"""
Quick test script to verify the new evaluation flow
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'evaluationWeb.settings')
django.setup()

from main.models import EvaluationPeriod, EvaluationResult, EvaluationHistory, Evaluation

print("=" * 70)
print("EVALUATION SYSTEM STATUS CHECK")
print("=" * 70)

# Check current evaluation periods
print("\n📅 EVALUATION PERIODS:")
periods = EvaluationPeriod.objects.filter(evaluation_type='student').order_by('-start_date')[:5]
for p in periods:
    status = "🟢 ACTIVE" if p.is_active else "⚫ INACTIVE"
    print(f"  {status} {p.name}")
    print(f"     Start: {p.start_date}")
    print(f"     End: {p.end_date}")

# Check evaluation forms status
print("\n📋 EVALUATION FORMS:")
student_evals = Evaluation.objects.filter(evaluation_type='student')
released_count = student_evals.filter(is_released=True).count()
total_count = student_evals.count()
print(f"  Total Forms: {total_count}")
print(f"  Released: {released_count}")
print(f"  Status: {'🟢 ACTIVE' if released_count > 0 else '⚫ CLOSED'}")

# Check current results (EvaluationResult table)
print("\n📊 CURRENT RESULTS (Profile Settings):")
current_results = EvaluationResult.objects.all()
print(f"  Total Records: {current_results.count()}")
if current_results.exists():
    latest_result = current_results.order_by('-calculated_at').first()
    print(f"  Latest Result: {latest_result.user.username} - {latest_result.evaluation_period.name}")
    print(f"     Score: {latest_result.total_percentage}%")
    print(f"     Responses: {latest_result.total_responses}")
else:
    print("  ⚠️  No current results (evaluation not ended yet or results need processing)")

# Check historical results (EvaluationHistory table)
print("\n📚 EVALUATION HISTORY:")
history_records = EvaluationHistory.objects.all()
print(f"  Total Archived Records: {history_records.count()}")
if history_records.exists():
    # Group by period
    periods_in_history = history_records.values_list('evaluation_period__name', flat=True).distinct()
    print(f"  Periods in History: {len(periods_in_history)}")
    for period_name in periods_in_history:
        count = history_records.filter(evaluation_period__name=period_name).count()
        print(f"     - {period_name}: {count} records")

# System recommendations
print("\n" + "=" * 70)
print("💡 SYSTEM STATUS SUMMARY:")
print("=" * 70)

active_period = EvaluationPeriod.objects.filter(evaluation_type='student', is_active=True).first()
if active_period and released_count > 0:
    print("✅ System is ACTIVE - Students can evaluate")
    print(f"   Current Period: {active_period.name}")
    print("   👉 Action: Wait for evaluations, then click UNRELEASE to process results")
elif not active_period and current_results.exists():
    print("✅ Evaluation ENDED - Results visible in profile settings")
    print(f"   Results Count: {current_results.count()}")
    print("   👉 Action: Click RELEASE to start new evaluation period")
elif not active_period and not current_results.exists():
    print("⚠️  System is IDLE - No active evaluation, no current results")
    print("   👉 Action: Click RELEASE to start first evaluation period")
else:
    print("⚠️  Unexpected state - Please review system status")

print("\n" + "=" * 70)
print("TEST COMPLETE")
print("=" * 70)
