#!/usr/bin/env python
"""
Manual evaluation history archival script.
Use this to archive existing results that weren't automatically archived.
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'evaluationWeb.settings')
django.setup()

from main.models import EvaluationHistory, EvaluationResult, EvaluationPeriod
from django.db.models import Q
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def archive_old_results():
    """Archive existing results that weren't automatically archived"""
    
    print("=" * 70)
    print("MANUAL EVALUATION HISTORY ARCHIVAL")
    print("=" * 70)
    
    # Get all inactive periods (old ones)
    inactive_periods = EvaluationPeriod.objects.filter(is_active=False).order_by('start_date')
    
    print(f"\nFound {inactive_periods.count()} inactive periods:")
    for period in inactive_periods:
        print(f"  - {period.name} (Type: {period.evaluation_type})")
    
    # Get all results
    all_results = EvaluationResult.objects.all()
    print(f"\nFound {all_results.count()} evaluation results total")
    
    # Check what's already in history
    history_count = EvaluationHistory.objects.count()
    print(f"Already in history: {history_count} records")
    
    if history_count == 0:
        print("\n⚠️  History is empty - starting archival...")
        
        # Archive results from the OLDEST period to history
        # Keep only the LATEST period in main_evaluationresult
        
        all_periods = list(EvaluationPeriod.objects.filter(is_active=False).order_by('start_date'))
        
        if len(all_periods) >= 2:
            # Archive all but the last one
            periods_to_archive = all_periods[:-1]
            latest_period = all_periods[-1]
            
            print(f"\nArchiving results from: {len(periods_to_archive)} older period(s)")
            print(f"Keeping current in main_evaluationresult from: {latest_period.name}")
            
            archived_count = 0
            for period in periods_to_archive:
                results = EvaluationResult.objects.filter(evaluation_period=period)
                print(f"\n  Processing {period.name}:")
                print(f"    Found {results.count()} results")
                
                for result in results:
                    try:
                        history = EvaluationHistory.create_from_result(result)
                        archived_count += 1
                        print(f"    ✓ Archived {result.user.username}: {result.total_percentage}%")
                    except Exception as e:
                        print(f"    ✗ Error archiving {result.user.username}: {str(e)}")
            
            print(f"\n✅ Successfully archived {archived_count} results!")
        else:
            print("\n⚠️  Not enough periods to archive (need at least 2)")
    else:
        print("✓ History already has records - no archival needed")
    
    # Show final status
    print("\n" + "=" * 70)
    print("FINAL STATUS:")
    print("=" * 70)
    print(f"EvaluationResult records: {EvaluationResult.objects.count()}")
    print(f"EvaluationHistory records: {EvaluationHistory.objects.count()}")
    
    if EvaluationHistory.objects.count() > 0:
        print("\nHistory contents:")
        for history in EvaluationHistory.objects.all().order_by('archived_at'):
            print(f"  - {history.user.username}: {history.total_percentage}% ({history.evaluation_period.name})")
    
    print("=" * 70)

if __name__ == "__main__":
    archive_old_results()
