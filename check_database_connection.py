"""
Check which database we're actually connected to
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'evaluationWeb.settings')
django.setup()

from django.conf import settings
from main.models import EvaluationResponse, User

print("\n" + "=" * 80)
print("DATABASE CONNECTION INFO")
print("=" * 80)

# Show database settings
db_config = settings.DATABASES['default']
print(f"\nDatabase Engine: {db_config['ENGINE']}")
print(f"Database Name: {db_config.get('NAME', 'N/A')}")
print(f"Database Host: {db_config.get('HOST', 'N/A')}")
print(f"Database Port: {db_config.get('PORT', 'N/A')}")
print(f"Database User: {db_config.get('USER', 'N/A')}")

# Check if we can see the evaluations from the screenshot
print("\n" + "=" * 80)
print("CHECKING FOR EVALUATIONS FROM SCREENSHOT")
print("=" * 80)

# Look for jowardclaudio
try:
    joward = User.objects.get(username='jowardclaudio')
    print(f"\n✅ Found jowardclaudio (ID: {joward.id})")
    responses = EvaluationResponse.objects.filter(evaluator=joward)
    print(f"   Evaluation responses: {responses.count()}")
    for resp in responses:
        print(f"   - Evaluated: {resp.evaluatee.username}")
except User.DoesNotExist:
    print("\n❌ jowardclaudio not found in this database")

# Look for aeroncaligagan being evaluated
try:
    aeron = User.objects.get(username='aeroncaligagan')
    print(f"\n✅ Found aeroncaligagan (ID: {aeron.id})")
    responses = EvaluationResponse.objects.filter(evaluatee=aeron)
    print(f"   Times evaluated: {responses.count()}")
    for resp in responses:
        print(f"   - By: {resp.evaluator.username} (Section: {resp.student_section})")
except User.DoesNotExist:
    print("\n❌ aeroncaligagan not found in this database")

# Total count
total_responses = EvaluationResponse.objects.count()
print(f"\n📊 TOTAL EVALUATION RESPONSES IN DATABASE: {total_responses}")

print("\n" + "=" * 80)
