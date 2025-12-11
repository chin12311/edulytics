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
        
        # Keywords for sentiment analysis
        positive_indicators = [
            'excellent', 'great', 'good', 'wonderful', 'amazing', 'helpful',
            'clear', 'engaging', 'knowledgeable', 'patient', 'friendly',
            'caring', 'supportive', 'effective', 'love', 'best', 'awesome',
            'fantastic', 'outstanding', 'brilliant', 'inspiring', 'dedicated'
        ]
        
        negative_indicators = [
            'poor', 'bad', 'terrible', 'worst', 'boring', 'confusing',
            'unclear', 'unfair', 'difficult', 'hard', 'hate', 'dislike',
            'unprofessional', 'rude', 'unhelpful', 'lazy', 'absent',
            'disorganized', 'disappointing', 'frustrating', 'inadequate',
            'abused', 'abuse'
        ]
        
        # Mixed/constructive feedback indicators
        mixed_indicators = [
            'but', 'however', 'although', 'sometimes', 'though',
            'could be', 'should be', 'would be better', 'except'
        ]
        
        # Count occurrences
        positive_count = sum(1 for word in positive_indicators if word in comment_lower)
        negative_count = sum(1 for word in negative_indicators if word in comment_lower)
        has_mixed_indicator = any(indicator in comment_lower for indicator in mixed_indicators)
        
        # Determine sentiment
        if (positive_count > 0 and negative_count > 0) or (has_mixed_indicator and (positive_count > 0 or negative_count > 0)):
            return 'mixed'
        elif positive_count > negative_count:
            return 'positive'
        elif negative_count > positive_count:
            return 'negative'
        else:
            return 'neutral'
    
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
                        "content": f"""Analyze these EXACT scores and provide SPECIFIC recommendations for {evaluation_type.upper()} evaluation data:

{context}

REQUIRED FORMAT FOR EACH RECOMMENDATION:
1. **Student Quote (Negative):** Include 1 actual negative/critical student comment
2. **Student Quote (Positive):** Include 1 actual positive student comment that shows their strength
3. **Question Analysis:** Reference specific evaluation questions that scored low (e.g., "Your score on 'explains concepts clearly' was 65%")
4. **What to do:** Provide 3-5 concrete action steps to improve

Focus on the WEAKEST areas first. Make it PERSONAL by showing real student voices.

IMPORTANT: 
- MUST include actual student quotes from the feedback provided
- MUST reference specific evaluation question results
- Make it engaging so the teacher actually wants to read it
- Balance criticism with recognition of strengths

Provide 3 SPECIFIC recommendations following this format."""
                    }
                ],
                max_tokens=1200,
                temperature=0.7
            )
            
            # Parse the AI response
            ai_content = response.choices[0].message.content
            print(f"🤖 AI Raw Response Preview: {ai_content[:200]}...")
            
            recommendations = self._parse_ai_response(ai_content, evaluation_type)
            
            # VALIDATE we got real recommendations, not generic ones
            if self._are_recommendations_generic(recommendations, evaluation_type):
                print(f"⚠️ AI returned generic recommendations for {evaluation_type}, using contextual fallback")
                return self._get_contextual_fallback(section_data, role, section_code, evaluation_type)
            
            print(f"✅ Generated {len(recommendations)} contextual recommendations for {evaluation_type} evaluation")
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

CRITICAL FORMAT FOR EACH RECOMMENDATION:
1. Start with actual student quote (if available): "Student said: [exact quote]"
2. Follow with what this means: "This indicates..."
3. Provide specific actions: "What to do: [concrete steps]"
4. Reference specific evaluation questions that scored low

IMPORTANT RULES:
- ALWAYS include at least 1 negative student comment quote and 1 positive student comment quote
- Make recommendations personal and hard to ignore by using real student voices
- Do NOT give generic advice - be specific to the actual scores and comments
- Reference specific evaluation questions (e.g., "Students rated 'explains concepts clearly' at 65%")
- Balance is key: Show what they're doing well AND what needs improvement

Analyze:
- Category scores (which teaching areas are weakest)
- Individual question scores (specific teaching behaviors)
- Student comments (actual student voices and concerns)
- Provide concrete, actionable steps tied to this specific data

Format: 3 specific recommendations, each including student quotes and question-based analysis."""

    def _prepare_ai_context(self, user, section_data, section_code, role, evaluation_type):
        """Prepare context with evaluation type support"""
        context_parts = []
        
        # Basic info
        context_parts.append(f"Educator: {user.get_full_name() or user.username}")
        context_parts.append(f"Role: {role}")
        context_parts.append(f"Evaluation Type: {evaluation_type.upper()}")
        
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
            for category, score, max_score, description in categories:
                percentage_of_max = (score / max_score * 100) if max_score > 0 else 0
                performance_level = "Excellent" if percentage_of_max >= 90 else "Good" if percentage_of_max >= 80 else "Average" if percentage_of_max >= 70 else "Needs Improvement"
                context_parts.append(f"• {category}: {score:.1f}% ({percentage_of_max:.1f}% of maximum) - {performance_level}")
                context_parts.append(f"  Focus: {description}")
        
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
                context_parts.append("\n💬 STUDENT FEEDBACK:")
                
                if positive_comments:
                    context_parts.append(f"\n✅ POSITIVE FEEDBACK ({len(positive_comments)} comments):")
                    for i, comment in enumerate(positive_comments[:5], 1):  # Limit to 5
                        context_parts.append(f"   {i}. \"{comment}\"")
                
                if negative_comments:
                    context_parts.append(f"\n❌ CRITICAL FEEDBACK ({len(negative_comments)} comments):")
                    for i, comment in enumerate(negative_comments[:5], 1):  # Limit to 5
                        context_parts.append(f"   {i}. \"{comment}\"")
                
                if mixed_comments:
                    context_parts.append(f"\n🔄 CONSTRUCTIVE/MIXED FEEDBACK ({len(mixed_comments)} comments):")
                    context_parts.append("   (These contain both positive and negative elements - most valuable for improvement)")
                    for i, comment in enumerate(mixed_comments[:5], 1):  # Limit to 5
                        context_parts.append(f"   {i}. \"{comment}\"")
        
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
        
        # Add general teaching recommendations to fill if needed
        teaching_recs = [
            {
                'title': 'Implement Data-Driven Improvement',
                'description': 'Use student evaluation data to create targeted improvement plans with measurable goals and regular progress monitoring.',
                'priority': 'Medium',
                'reason': 'Evidence-based teaching improvement strategy'
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
        print(f"   Raw text preview: {ai_text[:200]}...")
        
        recommendations = []
        
        # Try multiple parsing strategies
        
        # Strategy 1: Look for numbered recommendations with bold titles like "1. **Title:**"
        # Split by numbered patterns first
        pattern1 = r'(?:^|\n)(\d+[\.\)])\s*\*{0,2}([^\n]+?)\*{0,2}:?\s*\n((?:(?!\n\d+[\.\)]).)+)'
        matches1 = re.findall(pattern1, ai_text, re.MULTILINE | re.DOTALL)
        
        if matches1:
            print(f"   ✅ Found {len(matches1)} recommendations using pattern 1 (numbered with bold)")
            for i, match in enumerate(matches1[:3], 1):  # Limit to 3
                num = match[0]
                title = match[1].strip().replace('**', '').replace('*', '')
                description = match[2].strip()
                
                # Clean up title - remove parenthetical score info if present
                if '(' in title:
                    # Keep only the part before the parenthesis
                    title = title.split('(')[0].strip()
                
                recommendations.append({
                    'title': title,
                    'description': description if description else "Focus on improving this area based on evaluation feedback.",
                    'priority': 'High' if i == 1 else 'Medium' if i == 2 else 'Low'
                })
                print(f"   Rec {i}: '{title}' ({len(description)} chars)")
        
        # Strategy 2: Look for markdown headers like "### Title" or "## Title"
        if not recommendations:
            pattern2 = r'^#{1,3}\s+(.+?)$([\s\S]+?)(?=^#{1,3}|\Z)'
            matches2 = re.findall(pattern2, ai_text, re.MULTILINE)
            
            if matches2:
                print(f"   ✅ Found {len(matches2)} recommendations using pattern 2 (markdown headers)")
                for i, match in enumerate(matches2[:3], 1):
                    title = match[0].strip()
                    description = match[1].strip()
                    
                    recommendations.append({
                        'title': title,
                        'description': description if description else "Focus on improving this area based on evaluation feedback.",
                        'priority': 'High' if i == 1 else 'Medium' if i == 2 else 'Low'
                    })
                    print(f"   Rec {i}: '{title}' ({len(description)} chars)")
        
        # Strategy 3: Look for "**Number. Title**" format with content below
        if not recommendations:
            pattern3 = r'\*{2}(\d+)\.\s*([^*]+?)\*{2}\s*\n((?:(?!\*{2}\d+\.).)+)'
            matches3 = re.findall(pattern3, ai_text, re.MULTILINE | re.DOTALL)
            
            if matches3:
                print(f"   ✅ Found {len(matches3)} recommendations using pattern 3 (bold numbered)")
                for i, match in enumerate(matches3[:3], 1):
                    title = match[1].strip()
                    description = match[2].strip()
                    
                    recommendations.append({
                        'title': title,
                        'description': description if description else "Focus on improving this area based on evaluation feedback.",
                        'priority': 'High' if i == 1 else 'Medium' if i == 2 else 'Low'
                    })
                    print(f"   Rec {i}: '{title}' ({len(description)} chars)")
        
        # Fallback: Split by double newlines and take first 3 paragraphs
        if not recommendations:
            print(f"   ⚠️ Using fallback parsing strategy")
            paragraphs = [p.strip() for p in ai_text.split('\n\n') if p.strip() and len(p.strip()) > 20]
            for i, para in enumerate(paragraphs[:3], 1):
                lines = para.split('\n')
                title = lines[0].strip()[:100]  # First line as title
                description = '\n'.join(lines[1:]) if len(lines) > 1 else para
                
                # Clean title
                title = re.sub(r'^\d+[\.\)]\s*', '', title)
                title = title.replace('**', '').replace('*', '').replace('#', '').strip()
                
                recommendations.append({
                    'title': title,
                    'description': description,
                    'priority': 'High' if i == 1 else 'Medium' if i == 2 else 'Low'
                })
        
        print(f"   📊 Parsed {len(recommendations)} total recommendations")
        for i, rec in enumerate(recommendations, 1):
            print(f"      {i}. {rec['title'][:50]}... ({len(rec.get('description', ''))} chars)")
        
        return recommendations[:3]  # Return max 3
    
    def _get_role_specific_fallback(self, role, evaluation_type):
        """Get generic fallback when no evaluation data is available"""