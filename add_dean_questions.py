# Run this script to add dean evaluation questions
# python manage.py shell < add_dean_questions.py

from main.models import DeanEvaluationQuestion

# Delete existing questions
DeanEvaluationQuestion.objects.all().delete()

dean_questions = [
    # Mission
    "Demonstrates commitment to the institution's mission and values",
    "Effectively communicates the college/school's vision and goals to faculty",
    "Leads initiatives that align with the institution's mission",
    
    # Communion
    "Fosters a collaborative and inclusive work environment",
    "Actively listens to and addresses faculty concerns",
    "Promotes professional development and growth opportunities for faculty",
    
    # Excellence
    "Sets high standards for academic and administrative excellence",
    "Provides effective leadership in curriculum development and improvement",
    "Makes informed and timely decisions that benefit the college/school",
    "Manages resources efficiently and transparently",
    
    # Innovation
    "Encourages innovation in teaching and learning",
    "Supports research and creative activities",
    "Adapts to changes and challenges effectively",
    
    # Leadership & Management
    "Demonstrates strong leadership and management skills",
    "Maintains open and effective communication with faculty",
]

for i, question_text in enumerate(dean_questions, start=1):
    DeanEvaluationQuestion.objects.create(
        question_number=i,
        question_text=question_text,
        is_active=True
    )
    print(f"Added question {i}: {question_text}")

print(f"\n✅ Successfully added {len(dean_questions)} dean evaluation questions!")
