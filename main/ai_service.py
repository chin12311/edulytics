import openai
import json
import re
from django.conf import settings
from openai import OpenAI

class TeachingAIRecommendationService:
    """
    AI service for generating teaching recommendations using GPT-4o
    Can be used by Coordinator, Dean, and Faculty views with evaluation type support
    """
    
    def __init__(self):
        self.api_key = settings.OPENAI_API_KEY
        self.client = OpenAI(api_key=self.api_key)
    
    @staticmethod
    def analyze_comment_sentiment(comment):
        """
        Analyze sentiment of a comment to categorize as positive, negative, mixed, or neutral
        Returns: 'positive', 'negative', 'mixed', or 'neutral'
        """
        if not comment or not isinstance(comment, str):
            return 'neutral'
        
        comment_lower = comment.lower()
        
        # Keywords for sentiment analysis - EXPANDED
        positive_indicators = [
            'excellent', 'great', 'good', 'wonderful', 'amazing', 'helpful',
            'clear', 'engaging', 'knowledgeable', 'patient', 'friendly',
            'caring', 'supportive', 'effective', 'love', 'best', 'awesome',
            'fantastic', 'outstanding', 'brilliant', 'inspiring', 'dedicated',
            'like', 'enjoyed', 'appreciate', 'thank', 'professional', 'nice',
            'kind', 'understanding', 'thorough', 'organized', 'well', 'positive'
        ]
        
        negative_indicators = [
            'poor', 'bad', 'terrible', 'worst', 'boring', 'confusing',
            'unclear', 'unfair', 'difficult', 'hard', 'hate', 'dislike',
            'unprofessional', 'rude', 'unhelpful', 'lazy', 'absent',
            'disorganized', 'disappointing', 'frustrating', 'inadequate',
            'abused', 'abuse', 'strict', 'harsh', 'intimidating', 'mean',
            'slow', 'waste', 'useless', 'horrible', 'awful'
        ]
        
        # Mixed/constructive feedback indicators
        mixed_indicators = [
            'but', 'however', 'although', 'sometimes', 'though',
            'could be', 'should be', 'would be better', 'except',
            'needs', 'improve', 'wish'
        ]
        
        # Count occurrences
        positive_count = sum(1 for word in positive_indicators if word in comment_lower)
        negative_count = sum(1 for word in negative_indicators if word in comment_lower)
        has_mixed_indicator = any(indicator in comment_lower for indicator in mixed_indicators)
        
        # Determine sentiment
        # If has mixed indicator (like "but"), treat as mixed
        if has_mixed_indicator:
            return 'mixed'
        elif (positive_count > 0 and negative_count > 0):
            return 'mixed'
        elif positive_count > negative_count:
            return 'positive'
        elif negative_count > positive_count:
            return 'negative'
        else:
            # If no clear sentiment but has text, treat as mixed for review
            return 'mixed' if len(comment.strip()) > 10 else 'neutral'
    
    def get_recommendations(self, user, section_data=None, section_code=None, role="Educator", evaluation_type="student"):
        """Get AI-powered recommendations for any user role with evaluation type support"""
        print(f"🔍 AI Service Called - Section: {section_code}, Role: {role}, Evaluation Type: {evaluation_type}, Has Data: {section_data and section_data.get('has_data')}")
        
        try:
            # Prepare the context for the AI with evaluation type
            context = self._prepare_ai_context(user, section_data, section_code, role, evaluation_type)
            
            print(f"📝 AI Context Prepared - Section: {section_code}, Evaluation Type: {evaluation_type}")
            
            # Get the appropriate system prompt based on evaluation type
            system_prompt = self._get_system_prompt(evaluation_type)
            
            # Call GPT-4o
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "system",
                        "content": system_prompt
                    },
                    {
                        "role": "user",
                        "content": f"""Generate 3 recommendations based on this data:

{context}

🚨 CRITICAL INSTRUCTION 🚨
Look at the "STUDENT COMMENTS" section above. If student comments are provided:
- EVERY recommendation MUST start with: **Student Comment:** "A student said: [exact quote]"
- COPY the exact student comment text
- Then recommend a specific teaching method to address what the student said

If NO student comments are provided, state "No comments available" and base recommendations on scores only.

Generate 3 recommendations following the EXACT format from the system prompt:"""
                    }
                ],
                max_tokens=1500,
                temperature=0.7
            )
            
            # Parse the AI response
            ai_content = response.choices[0].message.content
            print(f"🤖 AI Raw Response Preview: {ai_content[:200]}...")
            
            recommendations = self._parse_ai_response(ai_content, evaluation_type)
            
            # Check if we got meaningful recommendations
            if not recommendations or len(recommendations) == 0:
                print(f"⚠️ No recommendations parsed, using contextual fallback")
                return self._get_contextual_fallback(section_data, role, section_code, evaluation_type)
            
            print(f"✅ Generated {len(recommendations)} AI recommendations for {evaluation_type} evaluation")
            return recommendations
            
        except Exception as e:
            print(f"❌ AI Recommendation Error for {evaluation_type}: {e}")
            import traceback
            traceback.print_exc()
            return self._get_contextual_fallback(section_data, role, section_code, evaluation_type)
    
    def _get_system_prompt(self, evaluation_type):
        """Get appropriate system prompt based on evaluation type"""
        if evaluation_type == "peer":
            return """You are an expert professional development consultant. Provide SPECIFIC, DATA-DRIVEN recommendations based EXACTLY on the PEER evaluation scores provided.

CRITICAL: For PEER evaluations, focus on:
- Professional collaboration and communication skills
- Workplace relationships and teamwork effectiveness  
- Professional responsibility and accountability
- Leadership presence and professional impact
- Workplace effectiveness and collegial relationships

PEER EVALUATION CATEGORIES:
1. Communication and Collaboration (35%): Effective communication, active listening, respect, team contribution
2. Responsibility and Professionalism (25%): Timely completion, reliability, initiative, institutional contribution  
3. Leadership and Work Ethic (20%): Leadership qualities, conflict resolution, feedback acceptance, focus, organization
4. Overall Professional Impact (20%): Work ethic, integrity, collaboration willingness

Do NOT give teaching-specific advice like "active learning" or "classroom management" for peer evaluations.

Analyze the category scores and provide recommendations that:
- Address the LOWEST scoring professional competency areas first
- Are specific to the actual percentage gaps in workplace skills
- Suggest concrete actions for improving professional relationships
- Are tailored to professional development and team effectiveness

Format: 3 specific recommendations with clear priorities based on the actual PEER evaluation data."""
        else:
            return """You are an expert educational consultant. Provide SPECIFIC, DATA-DRIVEN recommendations based EXACTLY on the STUDENT evaluation scores and feedback provided.

🎯 YOUR PRIMARY TASK: Base your recommendations on the ACTUAL STUDENT COMMENTS provided. Quote them directly!

CRITICAL - UNDERSTAND THE SCORING SYSTEM:
• Category scores are shown as "X% out of Y% maximum"
• Example: "22.5% out of 25% maximum" = 90% performance (EXCELLENT!)
• DO NOT interpret "22.5%" as low - it means they achieved 22.5 out of 25 possible points
• ALWAYS calculate: (score ÷ maximum) × 100 = actual performance percentage
• Performance levels:
  - 90%+ = Excellent (maintain and refine)
  - 80-89% = Good (minor improvements)
  - 70-79% = Average (moderate improvements needed)
  - Below 70% = Needs significant improvement

🚨 CRITICAL FORMAT - YOU MUST FOLLOW THIS EXACTLY 🚨

FOR EACH RECOMMENDATION, USE THIS EXACT STRUCTURE:

**1. [Action-Oriented Title Based on Student Feedback]**

**Student Comment:** "A student said: [COPY THE EXACT QUOTE FROM THE STUDENT COMMENTS SECTION BELOW]"

**Analysis:** This comment indicates [what the problem/strength is]

**Recommended Teaching Method:** [Name of specific pedagogy - e.g., "Think-Pair-Share", "Problem-Based Learning", "Formative Assessment"]

**Implementation Steps:**
1. [Specific action step addressing the student comment]
2. [Specific action step addressing the student comment]
3. [Specific action step addressing the student comment]

**Expected Outcome:** This approach should improve [specific category] score from X% to Y%

---

🎯 TEACHING METHODS TO RECOMMEND (choose based on student feedback):
- Active Learning: Think-Pair-Share, Jigsaw, Gallery Walk, Case Studies, Problem-Based Learning
- Engagement: Real-world examples, Interactive polls, Gamification, Storytelling
- Assessment: Formative quizzes, Peer feedback, Self-assessment rubrics, Exit tickets
- Classroom Management: Clear expectations, Positive reinforcement, Structured routines
- Communication: Office hours, Timely feedback, Weekly check-ins
- Content Delivery: Visual aids, Chunking content, Multiple examples, Pacing strategies

🚨 ABSOLUTE REQUIREMENTS 🚨
✓ EVERY recommendation MUST start with "Student Comment:" followed by an exact quote from below
✓ If NO student comments are provided below, then state "No student comments available" and base recommendations on scores only
✓ DO NOT make up fake student quotes
✓ DO NOT skip the student comment section
✓ Each recommendation must suggest a specific named teaching method
✓ Implementation steps must directly address what the student said

RANKING-BASED PERSONALIZATION:
• Top 3 Performers: Emphasize "maintaining your top position requires addressing [specific issue]"
• Middle Performers: Emphasize "moving from rank X to top 3 requires improving [specific area]"
• Lower Half: Emphasize "closing the gap with higher performers requires urgent action on [specific area]"

DO NOT:
✗ Give generic advice
✗ Make up or fabricate student comments if none are provided in the data
✗ Ignore the student comments if they ARE provided
✗ Forget to mention their ranking
✗ Recommend improvements for excellent scores (90%+)
✗ Use vague language like "try to improve" - be specific!

IMPORTANT: If no student comments are provided in the data, base your recommendations solely on:
1. Category scores and performance levels
2. The user's ranking compared to peers
3. Specific numerical data from evaluations

Analyze in this order:
1. RANKING - Where do they stand?
2. STUDENT COMMENTS (if available) - What are students actually saying?
3. CATEGORY SCORES - Which areas are weakest?
4. SPECIFIC ACTIONS - What concrete steps will address the data and improve scores?

Format: 3 specific recommendations. Include direct student quotes ONLY if they are provided in the data."""

    def _prepare_ai_context(self, user, section_data, section_code, role, evaluation_type):
        """Prepare context with evaluation type support"""
        context_parts = []
        
        # Basic info
        context_parts.append(f"Educator: {user.get_full_name() or user.username}")
        context_parts.append(f"Role: {role}")
        context_parts.append(f"Evaluation Type: {evaluation_type.upper()}")
        
        # Add ranking information if available - MAKE IT PROMINENT
        from main.views import calculate_user_ranking
        ranking_data = calculate_user_ranking(user)
        if ranking_data.get('rank'):
            context_parts.append("\n🏆 INSTITUTE RANKING (CRITICAL CONTEXT):")
            context_parts.append(f"   Current Rank: {ranking_data.get('rank')} out of {ranking_data.get('total_users')} {user.userprofile.role}s in {user.userprofile.institute}")
            context_parts.append(f"   Overall Performance Score: {ranking_data.get('overall_score')}%")
            
            # Add context about what this ranking means
            rank = ranking_data.get('rank')
            total = ranking_data.get('total_users')
            if rank <= 3:
                context_parts.append("   📊 STATUS: TOP PERFORMER - Focus on maintaining excellence and mentoring others")
            elif rank <= total * 0.5:
                context_parts.append("   📊 STATUS: ABOVE AVERAGE - Focus on reaching top-tier performance")
            else:
                context_parts.append("   📊 STATUS: BELOW AVERAGE - Focus on fundamental improvements with measurable goals")
        
        if section_code and section_code != 'Overall':
            context_parts.append(f"Section: {section_code}")
        else:
            context_parts.append("Scope: Overall evaluation across all sections")
        
        # Evaluation scores
        if section_data and section_data.get('has_data'):
            context_parts.append("\n📊 EVALUATION RESULTS:")
            context_parts.append(f"Overall Score: {section_data.get('total_percentage', 0)}%")
            context_parts.append(f"Total Evaluations: {section_data.get('evaluation_count', section_data.get('total_responses', 0))}")
            
            # Add individual question scores if available
            question_scores = section_data.get('question_scores', [])
            if question_scores:
                context_parts.append("\n📋 INDIVIDUAL QUESTION SCORES:")
                for q in question_scores:
                    question_text = q.get('question', 'Unknown')
                    score = q.get('score', 0)
                    percentage = q.get('percentage', 0)
                    context_parts.append(f"  • {question_text}: {percentage:.1f}% (Score: {score:.2f}/5)")
            
            # Different category names and descriptions based on evaluation type
            if evaluation_type == "peer":
                categories = [
                    ("Communication and Collaboration", section_data.get('category_scores', [0,0,0,0])[0], 35, 
                     "Effectively communicates, actively listens, shows respect, contributes to team discussions"),
                    ("Responsibility and Professionalism", section_data.get('category_scores', [0,0,0,0])[1], 25, 
                     "Completes duties on time, demonstrates reliability, takes initiative, contributes to institutional goals"),
                    ("Leadership and Work Ethic", section_data.get('category_scores', [0,0,0,0])[2], 20, 
                     "Shows leadership, resolves conflicts, accepts feedback, maintains focus, stays organized"),
                    ("Overall Professional Impact", section_data.get('category_scores', [0,0,0,0])[3], 20, 
                     "Strong work ethic, professional integrity, willingness to collaborate in future projects")
                ]
            else:
                categories = [
                    ("Mastery of Subject Matter", section_data.get('category_scores', [0,0,0,0])[0], 35, "Content knowledge, expertise, subject depth"),
                    ("Classroom Management", section_data.get('category_scores', [0,0,0,0])[1], 25, "Discipline, organization, student behavior"),
                    ("Compliance to Policies", section_data.get('category_scores', [0,0,0,0])[2], 20, "Rules adherence, procedures, requirements"),
                    ("Personality", section_data.get('category_scores', [0,0,0,0])[3], 20, "Communication, rapport, teaching style")
                ]
            
            context_parts.append("\n📈 CATEGORY BREAKDOWN:")
            context_parts.append("NOTE: Category scores are displayed as percentages out of their maximum weight.")
            context_parts.append("Example: A score of 22.50% out of 25% maximum = 90% performance (Excellent)")
            context_parts.append("")
            for category, score, max_score, description in categories:
                percentage_of_max = (score / max_score * 100) if max_score > 0 else 0
                performance_level = "🌟 Excellent" if percentage_of_max >= 90 else "✅ Good" if percentage_of_max >= 80 else "⚠️ Average" if percentage_of_max >= 70 else "🚨 Needs Improvement"
                
                # Make it crystal clear what the numbers mean
                context_parts.append(f"• {category}:")
                context_parts.append(f"  Score: {score:.1f}% out of {max_score}% maximum")
                context_parts.append(f"  Performance: {percentage_of_max:.1f}% - {performance_level}")
                context_parts.append(f"  Description: {description}")
                
                # Add interpretation
                if percentage_of_max >= 90:
                    context_parts.append(f"  ⭐ This is EXCELLENT - top tier performance in {category.lower()}")
                elif percentage_of_max >= 80:
                    context_parts.append(f"  ✓ This is GOOD - strong performance with minor room for improvement")
                elif percentage_of_max >= 70:
                    context_parts.append(f"  ⚠ This is AVERAGE - moderate improvement needed")
                else:
                    context_parts.append(f"  ❗ This NEEDS ATTENTION - significant improvement required")
                context_parts.append("")  # Blank line for readability
        
        else:
            context_parts.append("No specific evaluation data available for analysis.")
            context_parts.append("Providing general recommendations based on role and evaluation type.")
        
        # Add context based on evaluation type
        context_parts.append(f"\n🎯 CONTEXT:")
        context_parts.append("• Level: Higher Education")
        context_parts.append(f"• Role: {role}")
        context_parts.append(f"• Evaluation Type: {evaluation_type}")
        
        if evaluation_type == "peer":
            context_parts.append("• Focus: Professional collaboration, workplace relationships, and team effectiveness")
            context_parts.append("• Data Source: Peer evaluations from colleagues")
        else:
            context_parts.append("• Focus: Teaching effectiveness and student learning experience")
            context_parts.append("• Data Source: Student evaluations")
            
        if section_code and section_code != 'Overall':
            context_parts.append(f"• Current Focus: {section_code}")
            
        context_parts.append("• Goal: Provide specific, actionable recommendations based on actual evaluation data")
        
        # Add student comments if available (for student evaluations only)
        if evaluation_type == "student" and section_data:
            positive_comments = section_data.get('positive_comments', [])
            negative_comments = section_data.get('negative_comments', [])
            mixed_comments = section_data.get('mixed_comments', [])
            
            if positive_comments or negative_comments or mixed_comments:
                context_parts.append("\n" + "="*80)
                context_parts.append("🚨🚨🚨 STUDENT COMMENTS - QUOTE THESE IN YOUR RECOMMENDATIONS 🚨🚨🚨")
                context_parts.append("="*80)
                context_parts.append("")
                context_parts.append("YOU MUST USE THESE EXACT QUOTES IN YOUR RECOMMENDATIONS!")
                context_parts.append("Each recommendation should start with one of these student comments.")
                context_parts.append("")
                
                comments_added = 0
                max_comments = 2  # Limit to 1-2 most impactful comments
                
                # PRIORITY 1: Negative comments (most actionable - these drive improvement)
                if negative_comments and comments_added < max_comments:
                    # Select the most detailed negative comment
                    most_critical = max(negative_comments, key=len)
                    context_parts.append(f"STUDENT COMMENT #{comments_added + 1} (CRITICAL FEEDBACK):")
                    context_parts.append(f'"{most_critical}"')
                    context_parts.append("→ Recommend teaching methods to address this issue")
                    context_parts.append("")
                    comments_added += 1
                
                # PRIORITY 2: Mixed comments (contain both praise and improvement areas)
                if mixed_comments and comments_added < max_comments:
                    best_mixed = max(mixed_comments, key=len)
                    context_parts.append(f"STUDENT COMMENT #{comments_added + 1} (CONSTRUCTIVE FEEDBACK):")
                    context_parts.append(f'"{best_mixed}"')
                    context_parts.append("→ Recommend teaching methods that enhance what works")
                    context_parts.append("")
                    comments_added += 1
                
                # PRIORITY 3: Positive comments (only if no negative/mixed, or need balance)
                if positive_comments and comments_added < max_comments:
                    best_positive = max(positive_comments, key=len)
                    context_parts.append(f"STUDENT COMMENT #{comments_added + 1} (POSITIVE FEEDBACK):")
                    context_parts.append(f'"{best_positive}"')
                    context_parts.append("→ Recommend ways to maintain/replicate this success")
                    context_parts.append("")
                    comments_added += 1
                
                context_parts.append("="*80)
                context_parts.append("END OF STUDENT COMMENTS - USE THESE IN YOUR RECOMMENDATIONS")
                context_parts.append("="*80)
                context_parts.append("")
            else:
                # Explicitly state no comments are available
                context_parts.append("\n⚠️ NO STUDENT COMMENTS AVAILABLE")
                context_parts.append("Base your recommendations ONLY on:")
                context_parts.append("• Category scores and performance percentages")
                context_parts.append("• User's ranking compared to peers")
                context_parts.append("• Numerical data from evaluations")
                context_parts.append("DO NOT fabricate or make up student quotes!")
                context_parts.append("")
        
        return "\n".join(context_parts)
    
    def _are_recommendations_generic(self, recommendations, evaluation_type):
        """Check if recommendations are too generic for the evaluation type - LENIENT VERSION"""
        if not recommendations or len(recommendations) == 0:
            return True
        
        print(f"🔍 Validating {len(recommendations)} recommendations for {evaluation_type}")
            
        if evaluation_type == "peer":
            # Peer evaluation should NOT contain teaching-specific terms
            teaching_terms = [
                'classroom', 'student', 'teaching', 'lesson', 'homework', 'assignment', 
                'curriculum', 'syllabus', 'lecture', 'pedagogy', 'instructional', 
                'learning objectives', 'formative assessment', 'active learning',
                'differentiated instruction', 'student engagement', 'lesson plan'
            ]
            # Only reject if contains teaching terms
            for rec in recommendations:
                title_desc = f"{rec.get('title', '')} {rec.get('description', '')}".lower()
                if any(term in title_desc for term in teaching_terms):
                    print(f"❌ Found teaching term in peer recommendation: {title_desc[:100]}")
                    return True
            return False
        else:
            # For student evaluations - MUCH more lenient, only reject truly generic terms
            truly_generic = [
                'think-pair-share', 'exit tickets', 'minute papers',
                'jigsaw activities', 'fishbowl discussion'
            ]
            
            generic_count = 0
            for rec in recommendations:
                title_desc = f"{rec.get('title', '')} {rec.get('description', '')}".lower()
                
                # Count how many truly generic terms appear
                if any(term in title_desc for term in truly_generic):
                    generic_count += 1
                    print(f"⚠️ Found generic term in recommendation: {title_desc[:100]}")
            
            # Only reject if more than half contain generic terms
            is_generic = generic_count > len(recommendations) / 2
            print(f"📊 Generic check: {generic_count}/{len(recommendations)} generic -> {'REJECT' if is_generic else 'ACCEPT'}")
            return is_generic
    
    def _get_contextual_fallback(self, section_data, role, section_code=None, evaluation_type="student"):
        """Generate contextual fallback based on actual scores and evaluation type"""
        print(f"🔄 Using contextual fallback for {section_code}, Evaluation Type: {evaluation_type}")
        
        if not section_data or not section_data.get('has_data'):
            print("📊 No section data available, using role-specific fallback")
            return self._get_role_specific_fallback(role, evaluation_type)
        
        if evaluation_type == "peer":
            return self._get_peer_fallback_recommendations(section_data, role, section_code)
        else:
            return self._get_student_fallback_recommendations(section_data, role, section_code)
    
    def _get_peer_fallback_recommendations(self, section_data, role, section_code):
        """Get peer-specific fallback recommendations based on peer evaluation categories"""
        category_scores = section_data.get('category_scores', [0, 0, 0, 0])
        total_percentage = section_data.get('total_percentage', 0)
        
        # Peer evaluation categories mapped to your form structure
        peer_categories = [
            ("Communication and Collaboration", category_scores[0], 35, 
             ["Effective communication", "Active listening", "Respect in interactions", "Team contribution"]),
            ("Responsibility and Professionalism", category_scores[1], 25, 
             ["Timely completion", "Reliability", "Initiative", "Institutional contribution"]),
            ("Leadership and Work Ethic", category_scores[2], 20, 
             ["Leadership qualities", "Conflict resolution", "Feedback acceptance", "Focus and organization"]),
            ("Overall Professional Impact", category_scores[3], 20, 
             ["Work ethic", "Professional integrity", "Future collaboration willingness"])
        ]
        
        # Calculate performances and find weakest categories
        performances = []
        for i, (name, score, max_score, sub_areas) in enumerate(peer_categories):
            performance = (score / max_score * 100) if max_score > 0 else 0
            performances.append({
                'index': i, 
                'name': name, 
                'score': score, 
                'performance': performance,
                'sub_areas': sub_areas
            })
        
        # Sort by performance (lowest first)
        performances.sort(key=lambda x: x['performance'])
        
        recommendations = []
        weak_categories = [p for p in performances if p['performance'] < 80]
        
        # Generate recommendations based on weakest areas
        if weak_categories:
            weakest = weak_categories[0]
            
            if weakest['index'] == 0:  # Communication and Collaboration
                recommendations.append({
                    'title': 'Enhance Professional Communication Skills',
                    'description': f"Your communication and collaboration score is {weakest['score']:.1f}%. Focus on active listening in meetings, providing clear and timely updates to colleagues, and seeking clarification to ensure mutual understanding.",
                    'priority': 'High',
                    'reason': f"Based on {weakest['performance']:.1f}% performance in Communication and Collaboration from peer feedback"
                })
            elif weakest['index'] == 1:  # Responsibility and Professionalism
                recommendations.append({
                    'title': 'Strengthen Professional Accountability',
                    'description': f"With a {weakest['score']:.1f}% score in Responsibility and Professionalism, focus on consistently meeting deadlines, taking ownership of responsibilities, and proactively contributing to institutional goals. Document your contributions and follow through on commitments.",
                    'priority': 'High',
                    'reason': f"Based on {weakest['performance']:.1f}% performance in Responsibility and Professionalism from peer evaluations"
                })
            elif weakest['index'] == 2:  # Leadership and Work Ethic
                recommendations.append({
                    'title': 'Develop Leadership Presence and Impact',
                    'description': f"Your leadership and work ethic score of {weakest['score']:.1f}% indicates opportunity for growth. Take initiative in group projects, demonstrate strong organizational skills, and help resolve team conflicts constructively. Be more open to feedback and apply it for improvement.",
                    'priority': 'High',
                    'reason': f"Based on {weakest['performance']:.1f}% performance in Leadership and Work Ethic from colleague feedback"
                })
            else:  # Overall Professional Impact
                recommendations.append({
                    'title': 'Increase Professional Impact and Collegiality',
                    'description': f"Based on your {weakest['score']:.1f}% score in Overall Professional Impact, focus on demonstrating strong work ethic, maintaining professional integrity, and building relationships that make colleagues want to collaborate with you on future projects.",
                    'priority': 'High',
                    'reason': f"Based on {weakest['performance']:.1f}% performance in Overall Professional Impact from peer assessments"
                })
        
        # Add second weakest category if available
        if len(recommendations) < 3 and len(weak_categories) > 1:
            second_weakest = weak_categories[1]
            specific_advice = self._get_peer_specific_advice(second_weakest)
            recommendations.append({
                'title': f'Improve {second_weakest["name"]}',
                'description': f'Peer feedback shows opportunity in {second_weakest["name"].lower()} (score: {second_weakest["score"]:.1f}%). {specific_advice}',
                'priority': 'Medium',
                'reason': f"Based on {second_weakest['performance']:.1f}% performance in {second_weakest['name']} from colleague evaluations"
            })
        
        # Add peer-specific professional development recommendations
        peer_recs = [
            {
                'title': 'Seek Constructive Peer Feedback',
                'description': 'Regularly ask colleagues for specific feedback on your collaborative approach and professional contributions. Create an action plan based on their input and track your progress.',
                'priority': 'Medium',
                'reason': 'Professional development strategy based on peer evaluation context'
            },
            {
                'title': 'Build Cross-Functional Relationships',
                'description': 'Initiate collaborative projects with colleagues from different departments to broaden your professional network, gain diverse perspectives, and demonstrate institutional commitment.',
                'priority': 'Medium',
                'reason': 'Relationship building and professional growth strategy'
            }
        ]
        
        # Combine and ensure we have 3 recommendations
        while len(recommendations) < 3 and peer_recs:
            recommendations.append(peer_recs.pop(0))
        
        # Final fallback if still needed
        if len(recommendations) < 3:
            recommendations.append({
                'title': 'Develop Professional Presence',
                'description': 'Focus on building strong professional relationships through consistent communication, reliable follow-through, and constructive contributions to team efforts.',
                'priority': 'Medium',
                'reason': 'Fundamental professional development strategy'
            })
        
        print(f"🔄 Generated {len(recommendations)} peer evaluation fallback recommendations")
        return recommendations[:3]
    
    def _get_peer_specific_advice(self, category_data):
        """Get specific advice for peer evaluation categories"""
        advice_map = {
            "Communication and Collaboration": "Practice active listening techniques and ensure you understand colleagues' perspectives before responding. Make conscious efforts to contribute meaningfully to team discussions.",
            "Responsibility and Professionalism": "Set clear deadlines for yourself and communicate progress regularly. Take ownership of tasks and look for opportunities to contribute beyond your immediate responsibilities.",
            "Leadership and Work Ethic": "Volunteer for leadership roles in team projects and demonstrate strong organizational skills. Be proactive in addressing challenges and helping colleagues.",
            "Overall Professional Impact": "Focus on building trust with colleagues through consistent performance and professional integrity. Make yourself available for collaboration and mentorship opportunities."
        }
        return advice_map.get(category_data['name'], "Focus on specific skill development in this area through targeted professional development.")
    
    def _get_student_fallback_recommendations(self, section_data, role, section_code):
        """Get student-specific fallback recommendations"""
        # ... (keep your existing student evaluation fallback logic) ...
        category_scores = section_data.get('category_scores', [0, 0, 0, 0])
        total_percentage = section_data.get('total_percentage', 0)
        
        categories = [
            ("Mastery of Subject Matter", category_scores[0], 35),
            ("Classroom Management", category_scores[1], 25), 
            ("Compliance to Policies", category_scores[2], 20),
            ("Personality", category_scores[3], 20)
        ]
        
        # Calculate performances and find weakest categories
        performances = []
        for i, (name, score, max_score) in enumerate(categories):
            performance = (score / max_score * 100) if max_score > 0 else 0
            performances.append({'index': i, 'name': name, 'score': score, 'performance': performance})
        
        # Sort by performance (lowest first)
        performances.sort(key=lambda x: x['performance'])
        
        recommendations = []
        weak_categories = [p for p in performances if p['performance'] < 80]
        
        # Generate recommendations based on weakest areas
        if weak_categories:
            weakest = weak_categories[0]
            
            if weakest['index'] == 0:  # Mastery of Subject Matter
                recommendations.append({
                    'title': 'Enhance Content Depth and Expertise',
                    'description': f'Based on your {weakest["score"]:.1f}% score in Mastery of Subject Matter, focus on deepening content knowledge through advanced preparation and real-world applications specific to {section_code if section_code and section_code != "Overall" else "your subject"}.',
                    'priority': 'High' if weakest['performance'] < 80 else 'Medium',
                    'reason': f"Based on {weakest['performance']:.1f}% performance in Mastery of Subject Matter from student evaluations"
                })
            elif weakest['index'] == 1:  # Classroom Management
                recommendations.append({
                    'title': 'Strengthen Classroom Management Systems',
                    'description': f'Address your {weakest["score"]:.1f}% Classroom Management score by establishing clear routines and proactive engagement strategies tailored to {section_code if section_code and section_code != "Overall" else "your classroom"}.',
                    'priority': 'High' if weakest['performance'] < 80 else 'Medium',
                    'reason': f"Based on {weakest['performance']:.1f}% performance in Classroom Management from student evaluations"
                })
            elif weakest['index'] == 2:  # Compliance to Policies
                recommendations.append({
                    'title': 'Improve Policy Adherence and Procedures',
                    'description': f'With a {weakest["score"]:.1f}% Compliance score, systematically follow institutional policies and documentation requirements for {section_code if section_code and section_code != "Overall" else "course delivery"}.',
                    'priority': 'High' if weakest['performance'] < 80 else 'Medium',
                    'reason': f"Based on {weakest['performance']:.1f}% performance in Compliance to Policies from student evaluations"
                })
            else:  # Personality
                recommendations.append({
                    'title': 'Enhance Communication and Rapport Building',
                    'description': f'Based on your {weakest["score"]:.1f}% Personality score, develop stronger student relationships through improved communication and creating a positive climate in {section_code if section_code and section_code != "Overall" else "your teaching"}.',
                    'priority': 'High' if weakest['performance'] < 80 else 'Medium',
                    'reason': f"Based on {weakest['performance']:.1f}% performance in Personality from student evaluations"
                })
        
        # Add data-specific teaching recommendations to fill if needed
        if total_percentage < 70:
            teaching_recs = [
                {
                    'title': f'Address Critical Performance Gap (Currently {total_percentage:.1f}%)',
                    'description': f'Your overall evaluation score of {total_percentage:.1f}% requires immediate attention. Focus on the lowest-scoring category: {weakest["name"]} at {weakest["score"]:.1f}%. Schedule weekly self-assessment sessions and seek peer observations for targeted feedback.',
                    'priority': 'High',
                    'reason': f'Urgent action needed - performance below 70%'
                }
            ]
        elif total_percentage < 80:
            teaching_recs = [
                {
                    'title': f'Build on Current Performance ({total_percentage:.1f}%)',
                    'description': f'With a {total_percentage:.1f}% overall score, focus on elevating your weakest area: {weakest["name"]} ({weakest["score"]:.1f}%). Review successful strategies from your stronger categories and adapt them to improve this dimension.',
                    'priority': 'Medium',
                    'reason': f'Targeted improvement to reach excellence threshold (80%+)'
                }
            ]
        else:
            # For excellent performance (80%+), give general excellence maintenance advice
            teaching_recs = [
                {
                    'title': f'Maintain Excellence ({total_percentage:.1f}%)',
                    'description': f'Your {total_percentage:.1f}% overall score demonstrates excellent performance across all categories. Continue your current effective practices while exploring innovative teaching methods. Consider sharing your successful strategies with colleagues to elevate teaching quality across the institution.',
                    'priority': 'Low',
                    'reason': f'Excellence maintenance and continuous improvement'
                }
            ]
        
        while len(recommendations) < 3 and teaching_recs:
            recommendations.append(teaching_recs.pop(0))
        
        print(f"🔄 Generated {len(recommendations)} student evaluation fallback recommendations")
        return recommendations[:3]

    def _get_role_specific_fallback(self, role, evaluation_type="student"):
        """Provide role-specific general recommendations when no data is available"""
        if evaluation_type == "peer":
            # Peer evaluation fallbacks
            if role in ["Coordinator", "Dean", "Department Head"]:
                return [
                    {
                        'title': 'Develop Faculty Collaboration Systems',
                        'description': 'Create structured programs for peer mentoring, interdisciplinary collaboration, and professional community building to enhance team effectiveness.',
                        'priority': 'High',
                        'reason': 'Leadership role in fostering professional collaboration'
                    },
                    {
                        'title': 'Enhance Team Communication Protocols',
                        'description': 'Establish clear communication channels and meeting structures to improve information sharing and collaborative decision-making across departments.',
                        'priority': 'High',
                        'reason': 'Organizational communication improvement'
                    },
                    {
                        'title': 'Promote Professional Development Culture',
                        'description': 'Encourage continuous professional growth through workshops, peer learning groups, and leadership opportunities focused on workplace effectiveness.',
                        'priority': 'Medium',
                        'reason': 'Building learning organization culture'
                    }
                ]
            else:
                # Faculty/Staff peer evaluation fallbacks
                return [
                    {
                        'title': 'Build Strong Professional Networks',
                        'description': 'Develop meaningful collegial relationships through regular communication, collaboration, and mutual support across the institution.',
                        'priority': 'High',
                        'reason': 'Fundamental professional relationship building'
                    },
                    {
                        'title': 'Enhance Collaborative Communication',
                        'description': 'Practice active listening, clear expression of ideas, and constructive feedback in all professional interactions with colleagues.',
                        'priority': 'High',
                        'reason': 'Professional communication skills development'
                    },
                    {
                        'title': 'Develop Professional Leadership Skills',
                        'description': 'Take initiative in team projects, contribute to institutional goals, and mentor colleagues to strengthen your professional impact.',
                        'priority': 'Medium',
                        'reason': 'Professional growth and leadership development'
                    }
                ]
        else:
            # Student evaluation fallbacks (your existing logic)
            if role in ["Coordinator", "Dean", "Department Head"]:
                return [
                    {
                        'title': 'Develop Faculty Support Systems',
                        'description': 'Create structured mentoring programs and professional development opportunities tailored to departmental teaching needs.',
                        'priority': 'High'
                    },
                    {
                        'title': 'Implement Curriculum Alignment Strategies',
                        'description': 'Ensure course objectives, assessments, and instructional methods are aligned across the program for cohesive student learning.',
                        'priority': 'High'
                    },
                    {
                        'title': 'Establish Data-Driven Improvement Cycles',
                        'description': 'Use evaluation data to identify program strengths and areas for improvement, creating targeted intervention plans.',
                        'priority': 'Medium'
                    }
                ]
            else:
                return [
                    {
                        'title': 'Design Engaging Learning Experiences',
                        'description': 'Create interactive lessons that promote critical thinking and active student participation through varied instructional strategies.',
                        'priority': 'High'
                    },
                    {
                        'title': 'Develop Comprehensive Assessment Plans',
                        'description': 'Implement diverse assessment methods that accurately measure student learning and provide meaningful feedback for improvement.',
                        'priority': 'High'
                    },
                    {
                        'title': 'Build Strong Student Relationships',
                        'description': 'Establish positive rapport with students through effective communication, accessibility, and supportive learning environments.',
                        'priority': 'Medium'
                    }
                ]

    def _parse_ai_response(self, ai_text, evaluation_type):
        """Parse the AI response into structured recommendations - ENHANCED WITH REGEX"""
        import re
        
        print(f"📄 Parsing AI response for {evaluation_type} evaluation...")
        print(f"   Raw text preview: {ai_text[:300]}...")
        
        recommendations = []
        
        # Strategy 1: Split by horizontal rules or double line breaks to separate recommendations
        # Look for pattern: **Number. Title** followed by content
        sections = re.split(r'\n---+\n|\n={3,}\n', ai_text)
        
        for section in sections:
            section = section.strip()
            if len(section) < 50:  # Skip tiny sections
                continue
            
            # Extract title from first line with bold markdown or number
            title_match = re.search(r'\*{2}(\d+)\.\s*([^*\n]+?)\*{2}|^(\d+)\.\s*\*{2}([^*\n]+?)\*{2}|^#{1,3}\s+(.+?)$', section, re.MULTILINE)
            
            if title_match:
                # Get title from whichever group matched
                title = None
                for group in title_match.groups():
                    if group and not group.isdigit():
                        title = group.strip()
                        break
                
                if not title:
                    title = section.split('\n')[0].strip()
                
                # Get description (everything after the title line)
                lines = section.split('\n')
                desc_lines = []
                found_title = False
                
                for line in lines:
                    if not found_title:
                        if title in line:
                            found_title = True
                        continue
                    desc_lines.append(line)
                
                description = '\n'.join(desc_lines).strip()
                
                # Clean up title
                title = re.sub(r'^\d+[\.\)]\s*', '', title)
                title = title.replace('**', '').replace('*', '').replace('#', '').strip()
                title = title[:150]  # Limit title length
                
                if description:
                    recommendations.append({
                        'title': title,
                        'description': description,
                        'priority': 'High' if len(recommendations) == 0 else 'Medium' if len(recommendations) == 1 else 'Low'
                    })
                    print(f"   ✅ Parsed recommendation: '{title}' ({len(description)} chars)")
                    
                    if len(recommendations) >= 3:
                        break
        
        # Strategy 2: If strategy 1 didn't work, try numbered list parsing
        if not recommendations:
            print(f"   Trying numbered list parsing...")
            pattern = r'(?:^|\n)(?:\*{2})?(\d+)[\.\)]\s+(?:\*{2})?([^\n]+?)(?:\*{2})?\s*\n((?:(?!\n\d+[\.\)]).)+)'
            matches = re.findall(pattern, ai_text, re.MULTILINE | re.DOTALL)
            
            if matches:
                print(f"   ✅ Found {len(matches)} recommendations via numbered list")
                for i, match in enumerate(matches[:3], 1):
                    title = match[1].strip().replace('**', '').replace('*', '')
                    description = match[2].strip()
                    
                    recommendations.append({
                        'title': title[:150],
                        'description': description if description else "Review this area based on evaluation feedback.",
                        'priority': 'High' if i == 1 else 'Medium' if i == 2 else 'Low'
                    })
        
        # Strategy 3: Fallback - split by paragraphs
        if not recommendations:
            print(f"   ⚠️ Using paragraph fallback parsing")
            paragraphs = [p.strip() for p in ai_text.split('\n\n') if p.strip() and len(p.strip()) > 50]
            
            for i, para in enumerate(paragraphs[:3], 1):
                lines = para.split('\n')
                title = lines[0].strip()[:150]
                description = '\n'.join(lines[1:]) if len(lines) > 1 else para
                
                # Clean title
                title = re.sub(r'^\d+[\.\)]\s*', '', title)
                title = title.replace('**', '').replace('*', '').replace('#', '').strip()
                
                if title and description:
                    recommendations.append({
                        'title': title,
                        'description': description,
                        'priority': 'High' if i == 1 else 'Medium' if i == 2 else 'Low'
                    })
        
        print(f"   📊 Successfully parsed {len(recommendations)} recommendations")
        return recommendations
        for i, rec in enumerate(recommendations, 1):
            print(f"      {i}. {rec['title'][:50]}... ({len(rec.get('description', ''))} chars)")
        
        return recommendations[:3]  # Return max 3
    
    def _get_role_specific_fallback(self, role, evaluation_type):
        """Get generic fallback when no evaluation data is available"""