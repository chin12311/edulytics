from main.models import StudentUpwardEvaluationQuestion

# Delete existing questions first
StudentUpwardEvaluationQuestion.objects.all().delete()

# Category 1: Communication & Availability (3 questions)
questions = [
    "The coordinator communicates program announcements, changes, and requirements clearly and in a timely manner.",
    "The coordinator is accessible and approachable for consultations and concerns.",
    "The coordinator responds to student inquiries (via email, messaging, or in-person) promptly and adequately.",
    
    # Category 2: Academic Support & Program Management (3 questions)
    "The coordinator provides adequate guidance on academic planning (e.g., course scheduling, flowcharts).",
    "The coordinator effectively facilitates the resolution of academic concerns (e.g., grading issues, subject conflicts).",
    "The coordinator ensures that program activities (e.g., orientations, seminars) are well-organized and beneficial.",
    
    # Category 3: Student Advocacy & Welfare (3 questions)
    "The coordinator shows genuine concern for student welfare and acts as an effective liaison between students and higher administration.",
    "The coordinator handles student grievances and suggestions fairly and confidentially.",
    "The coordinator promotes an inclusive and supportive learning environment.",
    
    # Category 4: Professionalism & Leadership (3 questions)
    "The coordinator demonstrates professionalism, integrity, and respect in all interactions.",
    "The coordinator exhibits strong leadership in managing the program and student cohort.",
    "The coordinator encourages student engagement and participation in program development.",
]

# Create questions
for idx, question_text in enumerate(questions, start=1):
    StudentUpwardEvaluationQuestion.objects.create(
        question_number=idx,
        question_text=question_text,
        is_active=True
    )
    print(f"Added question {idx}: {question_text}")

print(f"\n✅ Successfully added {len(questions)} student upward evaluation questions!")
