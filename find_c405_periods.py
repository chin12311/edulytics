#!/usr/bin/env python
"""Find all C405 results across all periods"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'evaluationWeb.settings')
django.setup()

from main.models import EvaluationResult, EvaluationPeriod, Section

print("="*60)
print("C405 RESULTS ACROSS ALL PERIODS")
print("="*60)

try:
    c405 = Section.objects.get(code='C405')
    print(f'\n✅ Section found: {c405.code} (ID: {c405.id})')
    
    # Get all results for C405
    all_results = EvaluationResult.objects.filter(section=c405).select_related('evaluation_period', 'user')
    print(f'\nTotal C405 results: {all_results.count()}')
    
    if all_results.count() > 0:
        print('\nResults by period:')
        for result in all_results:
            period_name = result.evaluation_period.name if result.evaluation_period else "No Period"
            period_end = result.evaluation_period.end_date if result.evaluation_period else "N/A"
            print(f'  • {result.user.username}: {result.total_percentage:.2f}%')
            print(f'    Period: {period_name} (End: {period_end})')
            print(f'    Responses: {result.total_responses}')
            print()
    
    # Show all periods
    print('\n' + '='*60)
    print('ALL EVALUATION PERIODS:')
    print('='*60)
    all_periods = EvaluationPeriod.objects.filter(evaluation_type='student').order_by('-end_date')
    for p in all_periods:
        status = "ACTIVE" if p.is_active else "INACTIVE"
        print(f'\n{status}: {p.name}')
        print(f'  Start: {p.start_date}')
        print(f'  End: {p.end_date}')
        
        # Count results in this period
        results_count = EvaluationResult.objects.filter(evaluation_period=p).count()
        print(f'  Total results: {results_count}')
        
        # Count C405 results in this period
        c405_results = EvaluationResult.objects.filter(section=c405, evaluation_period=p).count()
        if c405_results > 0:
            print(f'  ✅ C405 results: {c405_results}')
        
except Section.DoesNotExist:
    print('❌ Section C405 not found')

print('\n' + '='*60)
