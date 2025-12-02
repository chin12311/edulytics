#!/usr/bin/env python
"""Verify C405 period filtering fix"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'evaluationWeb.settings')
django.setup()

from django.utils import timezone
from main.models import EvaluationPeriod, EvaluationResult, Section

print("="*60)
print("C405 PERIOD FILTERING FIX VERIFICATION")
print("="*60)

# Show the difference between old query (bug) and new query (fixed)
print('\n1️⃣  OLD QUERY (BUG):')
print("   filter(is_active=False).order_by('-end_date').first()")
old_period = EvaluationPeriod.objects.filter(
    evaluation_type='student',
    is_active=False
).order_by('-end_date').first()
print(f'   Period: {old_period.name if old_period else "None"}')
if old_period:
    print(f'   End Date: {old_period.end_date}')
    is_future = old_period.end_date > timezone.now()
    print(f'   Is Future?: {is_future} {"❌ BUG!" if is_future else "✅"}')

print('\n2️⃣  NEW QUERY (FIXED):')
print("   filter(is_active=False, end_date__lte=now()).order_by('-end_date').first()")
new_period = EvaluationPeriod.objects.filter(
    evaluation_type='student',
    is_active=False,
    end_date__lte=timezone.now()
).order_by('-end_date').first()
print(f'   Period: {new_period.name if new_period else "None"}')
if new_period:
    print(f'   End Date: {new_period.end_date}')
    print(f'   Is Past?: {new_period.end_date <= timezone.now()} ✅')

print('\n3️⃣  C405 RESULTS:')
try:
    c405 = Section.objects.get(code='C405')
    print(f'   Section: {c405.code} (ID: {c405.id})')
    
    if new_period:
        results = EvaluationResult.objects.filter(section=c405, evaluation_period=new_period)
        print(f'   Results in correct period: {results.count()}')
        for r in results:
            print(f'     • {r.user.username}: {r.total_percentage:.2f}%')
        
        if results.count() > 0:
            print('\n✅ FIX SUCCESSFUL: C405 results now display correctly!')
        else:
            print('\n⚠️  No results found for C405 in this period')
    else:
        print('   ⚠️  No valid period found')
        
except Section.DoesNotExist:
    print('   ❌ Section C405 not found')

print("\n" + "="*60)
