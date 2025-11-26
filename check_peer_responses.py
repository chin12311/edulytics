"""
Check peer evaluation responses to debug filtering
"""
import os
import sys
import django

sys.path.append('/home/ubuntu/edulytics')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'evaluationWeb.settings')
django.setup()

from main.models import EvaluationResponse, EvaluationPeriod

def main():
    # Get peer period
    peer_period = EvaluationPeriod.objects.filter(evaluation_type='peer').first()
    
    if not peer_period:
        print("No peer period found")
        return
    
    print(f"Peer Period: {peer_period.name}")
    print(f"Start: {peer_period.start_date}, End: {peer_period.end_date}")
    print()
    
    # Get all responses
    all_responses = EvaluationResponse.objects.all()
    print(f"Total responses in database: {all_responses.count()}")
    print()
    
    # Show each response
    print("=== ALL RESPONSES ===")
    for r in all_responses:
        print(f"ID: {r.id}")
        print(f"  Evaluator: {r.evaluator.username if r.evaluator else 'None'}")
        print(f"  Evaluatee: {r.evaluatee.username if r.evaluatee else 'None'}")
        print(f"  Student Section: {r.student_section}")
        print(f"  Submitted: {r.submitted_at}")
        print(f"  Question 1: {r.question1}")
        print()
    
    # Filter by period
    period_responses = EvaluationResponse.objects.filter(
        submitted_at__gte=peer_period.start_date,
        submitted_at__lte=peer_period.end_date
    )
    print(f"=== RESPONSES IN PEER PERIOD ===")
    print(f"Count: {period_responses.count()}")
    for r in period_responses:
        print(f"  ID {r.id}: {r.evaluator.username} -> {r.evaluatee.username}, Section: {r.student_section}")
    print()
    
    # Filter by Staff
    staff_responses = period_responses.filter(student_section__icontains="Staff")
    print(f"=== RESPONSES WITH 'Staff' IN SECTION ===")
    print(f"Count: {staff_responses.count()}")
    for r in staff_responses:
        print(f"  ID {r.id}: {r.student_section}")

if __name__ == '__main__':
    main()
