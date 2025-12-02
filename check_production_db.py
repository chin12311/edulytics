"""
SSH into production server and check evaluation state
"""
import subprocess
import sys

# SSH command to check production database
ssh_command = [
    'ssh',
    '-i', r'C:\Users\ADMIN\.ssh\edulytics-key.pem',
    'ubuntu@13.211.104.201',
    'cd /home/ubuntu/evaluation && source venv/bin/activate && python manage.py shell -c "from main.models import EvaluationResponse, EvaluationResult, EvaluationPeriod; print(f\'Responses: {EvaluationResponse.objects.count()}\'); print(f\'Results: {EvaluationResult.objects.count()}\'); print(f\'Active Periods: {EvaluationPeriod.objects.filter(is_active=True).count()}\'); periods = EvaluationPeriod.objects.all().order_by(\'-start_date\')[:3]; [print(f\'Period: {p.name}, Active: {p.is_active}, Type: {p.evaluation_type}\') for p in periods]"'
]

print("Checking production database...")
print("=" * 80)

result = subprocess.run(ssh_command, capture_output=True, text=True, shell=True)
print(result.stdout)
if result.stderr:
    print("STDERR:", result.stderr)
