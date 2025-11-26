"""
Reprocess peer evaluation results with new simple averaging calculation
"""
import os
import sys
import django

# Add parent directory to path
sys.path.append('/home/ubuntu/edulytics')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'evaluationWeb.settings')
django.setup()

from main.models import EvaluationPeriod, EvaluationResult
from main.views import process_evaluation_results_for_user

def main():
    # Get peer evaluation period
    peer_period = EvaluationPeriod.objects.filter(evaluation_type='peer').first()
    
    if not peer_period:
        print("No peer evaluation period found")
        return
    
    print(f"Found peer period: {peer_period.name}")
    print(f"Currently active: {peer_period.is_active}")
    
    # Activate if needed
    if not peer_period.is_active:
        peer_period.is_active = True
        peer_period.save()
        print("Activated peer period")
    
    # Get results that need reprocessing
    results = EvaluationResult.objects.filter(evaluation_period=peer_period)
    print(f"\nFound {results.count()} results to reprocess")
    
    # Show old scores
    print("\n=== OLD SCORES ===")
    for result in results:
        print(f"{result.user.username}: {result.total_percentage}%")
    
    # Reprocess each result
    print("\n=== REPROCESSING ===")
    for result in results:
        print(f"Reprocessing for: {result.user.username}")
        process_evaluation_results_for_user(result.user, peer_period)
    
    # Check new scores
    print("\n=== NEW SCORES ===")
    updated_results = EvaluationResult.objects.filter(evaluation_period=peer_period)
    for res in updated_results:
        print(f"{res.user.username}: {res.total_percentage}%")

if __name__ == '__main__':
    main()
