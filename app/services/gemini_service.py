"""
Service for interacting with Google Gemini API.
"""
import json
import logging
from google import genai
from google.genai import types
from flask import current_app
from app.models import InterviewSession, ResumeProfile

logger = logging.getLogger(__name__)

def get_client(api_key: str) -> genai.Client:
    """Helper to initialize the Gemini client."""
    return genai.Client(api_key=api_key)

def validate_api_key(api_key: str) -> bool:
    """Makes a minimal test call to Gemini to verify key validity."""
    try:
        client = get_client(api_key)
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents='Return the word OK'
        )
        return 'OK' in response.text
    except Exception as e:
        logger.error(f"API key validation failed: {e}")
        return False

def analyze_resume(api_key: str, resume_text: str) -> dict:
    """Sends resume text to Gemini to extract structured resume data."""
    client = get_client(api_key)
        
    prompt = f"""
    Extract structured information from the following resume text.
    Return ONLY a JSON object with the following exact keys:
    "skills", "education", "experience", "projects", "certifications", 
    "technologies", "strengths", "career_level", "summary".
    Each value should be a string, list, or appropriate JSON structure.
    Do not use markdown blocks around the JSON.
    
    Resume Text:
    {resume_text}
    """
    
    try:
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json"
            )
        )
        return json.loads(response.text)
    except Exception as e:
        logger.error(f"Failed to analyze resume: {e}")
        return {
            "skills": [], "education": [], "experience": [], 
            "projects": [], "certifications": [], "technologies": [], 
            "strengths": [], "career_level": "Unknown", "summary": ""
        }

def generate_interview_question(api_key: str, context: dict, session: InterviewSession) -> dict:
    """Generates next interview question based on compressed context."""
    client = get_client(api_key)
    
    system_instruction = f"""
    You are an expert interviewer for a {session.job_role} position at {session.company_name}.
    Your persona is: {session.interviewer_persona}.
    You must maintain your persona completely and never break character.
    Keep your questions conversational and concise. Never repeat previous questions.
    Follow this distribution across the whole interview:
    40% company-specific, 30% resume-based, 20% role-specific, 10% follow-up.
    
    Current Stage: {session.current_stage}
    
    Return ONLY a JSON object with:
    "question": the actual question text to speak to the user,
    "category": the category of this question,
    "stage": the stage of the interview it belongs to.
    Do not use markdown formatting.
    """
    
    user_message = f"""
    Here is the interview context:
    {json.dumps(context)}
    
    Please ask the next best question for the candidate.
    """
    
    try:
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=user_message,
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
                response_mime_type="application/json"
            )
        )
        return json.loads(response.text)
    except Exception as e:
        logger.error(f"Failed to generate question: {e}")
        return {
            "question": "Could you tell me more about your experience?",
            "category": "role-specific",
            "stage": session.current_stage or "resume_discussion"
        }

def evaluate_answer(api_key: str, context: dict, question: str, answer: str, session: InterviewSession) -> dict:
    """Evaluates candidate answer and determines adaptive behavior."""
    client = get_client(api_key)
    
    system_instruction = """
    You are evaluating a candidate's answer.
    Determine how strong the answer is, provide brief internal notes, formulate a natural conversational response,
    and decide if a follow-up is needed based on this adaptive strategy:
    - strong -> deeper probing (follow up on complex detail)
    - average -> ask for examples (clarifying follow up)
    - weak -> explain and guide (reframe question)
    - incorrect -> correct gently and model answer.
    
    Return ONLY a JSON object with:
    "evaluation_label": "strong", "average", "weak", or "incorrect",
    "ai_notes": "your internal analysis of the answer",
    "ai_response": "your spoken response to the candidate before asking the next question",
    "follow_up_needed": boolean
    Do not use markdown formatting.
    """
    
    user_message = f"""
    Question asked: {question}
    Candidate's Answer: {answer}
    """
    
    try:
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=user_message,
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
                response_mime_type="application/json"
            )
        )
        return json.loads(response.text)
    except Exception as e:
        logger.error(f"Failed to evaluate answer: {e}")
        return {
            "evaluation_label": "average",
            "ai_notes": "Error evaluating answer.",
            "ai_response": "Thanks for sharing that.",
            "follow_up_needed": False
        }

def generate_feedback_report(api_key: str, session: InterviewSession, turns: list) -> dict:
    """Generates comprehensive feedback with all scores and detailed feedback sections."""
    client = get_client(api_key)
    
    turns_data = [
        {"Q": turn.question_text, "A": turn.answer_text, "Eval": turn.evaluation_label} 
        for turn in turns
    ]
    
    system_instruction = """
    You are an expert career coach providing a detailed feedback report for an interview.
    Analyze the full transcript and generate comprehensive scores (0-100) and insights.
    Return ONLY a JSON object with the following exact keys:
    "overall_score", "communication_score", "technical_score", "confidence_score", 
    "problem_solving_score", "leadership_score", "behavioral_score",
    "strengths" (list of strings),
    "weaknesses" (list of strings),
    "missed_opportunities" (list of strings),
    "suggested_answers" (dict mapping question to a better answer),
    "company_specific_recommendations" (list of strings),
    "improvement_plan" (list of strings),
    "communication_insights" (list of strings).
    Do not use markdown formatting.
    """
    
    user_message = f"""
    Job Role: {session.job_role} at {session.company_name}
    Interview Type: {session.interview_type}
    
    Transcript:
    {json.dumps(turns_data)}
    """
    
    try:
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=user_message,
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
                response_mime_type="application/json"
            )
        )
        return json.loads(response.text)
    except Exception as e:
        logger.error(f"Failed to generate feedback: {e}")
        return {
            "overall_score": 0, "communication_score": 0, "technical_score": 0, 
            "confidence_score": 0, "problem_solving_score": 0, "leadership_score": 0, 
            "behavioral_score": 0, "strengths": [], "weaknesses": [], 
            "missed_opportunities": [], "suggested_answers": {}, 
            "company_specific_recommendations": [], "improvement_plan": [], 
            "communication_insights": []
        }

def generate_resume_suggestions(api_key: str, resume_profile: ResumeProfile, feedback_reports: list) -> list:
    """Generates AI suggestions for resume improvement based on interview feedback."""
    client = get_client(api_key)
    
    feedbacks_summary = []
    for report in feedback_reports:
        feedbacks_summary.extend(report.weaknesses if report.weaknesses else [])
        feedbacks_summary.extend(report.missed_opportunities if report.missed_opportunities else [])
        
    system_instruction = """
    You are an expert resume writer. Given a resume profile and a list of identified weaknesses and missed opportunities from recent mock interviews, suggest 3-5 specific, actionable improvements for the resume.
    Return ONLY a JSON array of strings, where each string is a distinct suggestion.
    Do not use markdown formatting.
    """
    
    user_message = f"""
    Resume Details:
    Skills: {resume_profile.skills}
    Experience: {resume_profile.experience}
    
    Interview Weaknesses & Missed Opportunities:
    {json.dumps(feedbacks_summary)}
    """
    
    try:
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=user_message,
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
                response_mime_type="application/json"
            )
        )
        return json.loads(response.text)
    except Exception as e:
        logger.error(f"Failed to generate resume suggestions: {e}")
        return []
