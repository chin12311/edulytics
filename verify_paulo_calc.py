# Verify correct calculation with proper rating mapping

rating_to_numeric = {
    'Strongly Disagree': 1,
    'Disagree': 2,
    'Neutral': 3,
    'Agree': 4,
    'Strongly Agree': 5
}

# Paulo's evaluation ratings:
ratings = [
    'Agree',           # Q1 = 4
    'Agree',           # Q2 = 4
    'Strongly Agree',  # Q3 = 5
    'Agree',           # Q4 = 4
    'Agree',           # Q5 = 4
    'Strongly Agree',  # Q6 = 5
    'Agree',           # Q7 = 4
    'Agree',           # Q8 = 4
    'Strongly Agree',  # Q9 = 5
    'Agree',           # Q10 = 4
    'Agree',           # Q11 = 4
    'Strongly Agree',  # Q12 = 5
    'Agree',           # Q13 = 4
    'Agree',           # Q14 = 4
    'Strongly Agree',  # Q15 = 5
]

total_score = sum(rating_to_numeric[r] for r in ratings)
max_possible = 15 * 5  # 75
percentage = (total_score / max_possible) * 100

print("Paulo Madrigal's Dean Evaluation Calculation:")
print("=" * 60)
for i, rating in enumerate(ratings, 1):
    score = rating_to_numeric[rating]
    print(f"Q{i:2d}: {rating:20s} = {score}")

print("\n" + "=" * 60)
print(f"Total Score: {total_score}/{max_possible}")
print(f"Percentage: {percentage:.2f}%")
print("=" * 60)
