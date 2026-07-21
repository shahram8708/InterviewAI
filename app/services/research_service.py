"""
Service for researching companies.
"""
import json
import logging
from google import genai
from google.genai import types

logger = logging.getLogger(__name__)

def research_company(api_key: str, company_name: str, job_role: str, experience_level: str) -> dict:
    """Uses Gemini with Google Search grounding to research the company."""
    if not company_name or company_name.lower() in ["unknown", "n/a", "none"]:
        return {
            "interview_patterns": [],
            "common_questions": [],
            "culture_notes": "General industry culture.",
            "recent_news": [],
            "hiring_process": "Standard interview process.",
            "role_expectations": "Standard expectations for this role."
        }
        
    client = genai.Client(api_key=api_key)
    
    system_instruction = """
    You are an expert technical recruiter and career coach.
    Provide comprehensive research about the target company for interview preparation.
    Return ONLY a JSON object with the exact keys:
    "interview_patterns" (list of strings),
    "common_questions" (list of strings),
    "culture_notes" (string),
    "recent_news" (list of strings),
    "hiring_process" (string),
    "role_expectations" (string).
    Do not use markdown formatting.
    """
    
    user_message = f"""
    Research the following company and role for interview preparation:
    Company: {company_name}
    Job Role: {job_role}
    Experience Level: {experience_level}
    """
    
    try:
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=user_message,
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
                response_mime_type="application/json",
                tools=[types.Tool(google_search=types.GoogleSearch())]
            )
        )
        return json.loads(response.text)
    except Exception as e:
        logger.error(f"Failed to research company: {e}")
        return {
            "interview_patterns": ["Standard behavioral and technical rounds"],
            "common_questions": ["Tell me about yourself", "Why this company?"],
            "culture_notes": f"Research on {company_name} is currently unavailable.",
            "recent_news": [],
            "hiring_process": "Standard multi-stage process.",
            "role_expectations": f"Standard expectations for {job_role}."
        }
