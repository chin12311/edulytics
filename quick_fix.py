#!/usr/bin/env python
"""Quick fix for broken peer evaluation"""
import os, sys, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
sys.path.insert(0, '.')
django.setup()

from main.models import EvaluationPeriod, Evaluation

print('Deactivating all peer periods...')
EvaluationPeriod.objects.filter(evaluation_type='peer').update(is_active=False)

print('Activating period ID=4...')
period = EvaluationPeriod.objects.get(id=4)
period.is_active = True
period.save()

print(f'Linking orphaned evaluations to period {period.id}...')
orphaned = Evaluation.objects.filter(evaluation_type='peer', is_released=True, evaluation_period__isnull=True)
count = orphaned.count()
orphaned.update(evaluation_period=period)
print(f'Linked {count} orphaned evaluations')

print('\nVerifying...')
verified = Evaluation.objects.filter(evaluation_type='peer', is_released=True, evaluation_period=period).first()
active_period = EvaluationPeriod.objects.filter(evaluation_type='peer', is_active=True).first()
print(f'✅ Active peer period: ID={active_period.id if active_period else "None"}')
print(f'✅ Released peer evaluation: ID={verified.id if verified else "None"}')
print('DONE!')
