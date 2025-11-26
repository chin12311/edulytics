"""
Check and fix evaluation period assignments
"""
import os
import sys
import django

sys.path.append('/home/ubuntu/edulytics')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'evaluationWeb.settings')
django.setup()

from main.models import EvaluationPeriod, EvaluationResponse

def main():
    print("=== EVALUATION PERIODS ===")
    periods = EvaluationPeriod.objects.all()
    for p in periods:
        print(f"ID {p.id}: {p.name} ({p.evaluation_type})")
        print(f"  Active: {p.is_active}")
        print(f"  Start: {p.start_date}")
        print(f"  End: {p.end_date}")
        print()
    
    print("=== EVALUATION RESPONSES ===")
    responses = EvaluationResponse.objects.all()
    for r in responses:
        print(f"ID {r.id}: {r.evaluator.username} -> {r.evaluatee.username}")
        print(f"  Period ID: {r.evaluation_period_id}")
        if r.evaluation_period:
            print(f"  Period: {r.evaluation_period.name} ({r.evaluation_period.evaluation_type})")
        print(f"  Section: {r.student_section}")
        print(f"  Submitted: {r.submitted_at}")
        print()

if __name__ == '__main__':
    main()
