#!/usr/bin/env python
"""Check C405 raw responses"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'evaluationWeb.settings')
django.setup()

from main.models import EvaluationResponse, Section

print("="*60)
print("C405 RAW RESPONSES CHECK")
print("="*60)

try:
    c405 = Section.objects.get(code='C405')
    print(f'\n✅ Section: {c405.code} (ID: {c405.id})')
    
    responses = EvaluationResponse.objects.filter(section=c405)
    print(f'\nTotal responses: {responses.count()}')
    
    if responses.count() > 0:
        instructors = {}
        for r in responses:
            username = r.instructor.user.username
            if username not in instructors:
                instructors[username] = 0
            instructors[username] += 1
        
        print('\nResponses by instructor:')
        for username, count in instructors.items():
            print(f'  • {username}: {count} responses')
        
        print('\n💡 INTERPRETATION:')
        print('   Raw responses exist but have NOT been processed into EvaluationResult.')
        print('   Admin needs to click "Unrelease" button to process responses.')
    else:
        print('\n❌ No responses found for C405')
        
except Section.DoesNotExist:
    print('❌ Section C405 not found')

print('\n' + '='*60)
