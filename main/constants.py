# =============================================================================
# EVALUATION SYSTEM CONSTANTS
# =============================================================================
# Centralized configuration for all evaluation system constants
# Allows easy adjustment of business logic without modifying multiple files

# ===== CATEGORY WEIGHTS =====
# These weights determine how each evaluation category contributes to overall score
# Total must equal 1.0 (100%)
CATEGORY_WEIGHTS = {
    'mastery_of_subject_matter': 0.35,      # Category A - Questions 1-4
    'classroom_management': 0.25,            # Category B - Questions 5-8
    'compliance_to_policies': 0.20,          # Category C - Questions 9-12
    'personality': 0.20                      # Category D - Questions 13-15
}

# Ordered list for consistent iteration
CATEGORY_WEIGHTS_ORDERED = [
    ('mastery_of_subject_matter', 0.35),
    ('classroom_management', 0.25),
    ('compliance_to_policies', 0.20),
    ('personality', 0.20)
]

# Maximum scores for each category (as weights translated to max points)
CATEGORY_MAX_SCORES = {
    'mastery_of_subject_matter': 35,
    'classroom_management': 25,
    'compliance_to_policies': 20,
    'personality': 20
}

# ===== RATING SYSTEM =====
RATING_NUMERIC_MAP = {
    'Poor': 1,
    'Unsatisfactory': 2,
    'Satisfactory': 3,
    'Very Satisfactory': 4,
    'Outstanding': 5
}

RATING_NUMERIC_REVERSE = {
    1: 'Poor',
    2: 'Unsatisfactory',
    3: 'Satisfactory',
    4: 'Very Satisfactory',
    5: 'Outstanding'
}

MAX_RATING_SCORE = 5  # Ratings are on a scale of 1-5

# ===== PERFORMANCE THRESHOLDS =====
# Used for determining recommendation priority and performance classification
PERFORMANCE_EXCELLENT_THRESHOLD = 90  # >= 90% is excellent
PERFORMANCE_ACCEPTABLE_THRESHOLD = 80  # >= 80% is acceptable, < 80% needs improvement
PERFORMANCE_WEAK_THRESHOLD = 75  # < 75% is considered weak overall performance

# ===== EVALUATION QUESTIONS =====
# Question mappings to categories
QUESTIONS_BY_CATEGORY = {
    'mastery_of_subject_matter': range(1, 5),      # Questions 1-4
    'classroom_management': range(5, 9),           # Questions 5-8
    'compliance_to_policies': range(9, 13),        # Questions 9-12
    'personality': range(13, 16)                   # Questions 13-15
}

TOTAL_QUESTIONS = 15

# ===== EVALUATION PASSING SCORE =====
# Minimum score required to pass an evaluation
EVALUATION_PASSING_SCORE = 70.0

# Maximum number of consecutive evaluation failures allowed
MAX_FAILURE_ATTEMPTS = 2

# ===== CATEGORY DISPLAY NAMES =====
CATEGORY_DISPLAY_NAMES = {
    'mastery_of_subject_matter': 'Mastery of Subject Matter',
    'classroom_management': 'Classroom Management',
    'compliance_to_policies': 'Compliance to Policies',
    'personality': 'Personality'
}

# ===== PEER EVALUATION CATEGORIES =====
# Categories for peer/colleague evaluations
PEER_EVALUATION_CATEGORIES = {
    'communication_collaboration': 25,
    'responsibility_professionalism': 25,
    'leadership_work_ethic': 25,
    'overall_professional_impact': 25
}

PEER_CATEGORY_DISPLAY_NAMES = {
    'communication_collaboration': 'Communication and Collaboration',
    'responsibility_professionalism': 'Responsibility and Professionalism',
    'leadership_work_ethic': 'Leadership and Work Ethic',
    'overall_professional_impact': 'Overall Professional Impact'
}

# ===== PASSWORD REQUIREMENTS =====
MIN_PASSWORD_LENGTH = 8
REQUIRE_PASSWORD_COMPLEXITY = True  # Should include upper, lower, digits, special chars

# ===== PAGINATION =====
ITEMS_PER_PAGE = 25

# ===== RATING DISTRIBUTION DISPLAY =====
# For visualization purposes
RATING_DISTRIBUTION_COLORS = {
    'Poor': '#dc3545',                    # Red
    'Unsatisfactory': '#fd7e14',          # Orange
    'Satisfactory': '#ffc107',            # Yellow
    'Very Satisfactory': '#28a745',       # Green
    'Outstanding': '#007bff'              # Blue
}

# ===== EMAIL ALERTS =====
ENABLE_EMAIL_ALERTS = True
SCHOOL_HEAD_EMAIL = None  # Set from environment or settings
