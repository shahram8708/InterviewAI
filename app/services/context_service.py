"""
Service for managing interview context.
"""
import logging
from app.models import InterviewSession, ResumeProfile

logger = logging.getLogger(__name__)

def build_initial_context(resume_profile: ResumeProfile, session: InterviewSession) -> dict:
    """Create initial compressed context from resume profile and session config."""
    return {
        "job_role": session.job_role,
        "company_name": session.company_name,
        "experience_level": session.experience_level,
        "interview_type": session.interview_type,
        "candidate_summary": resume_profile.summary,
        "candidate_skills": resume_profile.skills,
        "candidate_experience": resume_profile.experience,
        "running_strengths": [],
        "running_weaknesses": [],
        "exchanges": []
    }

def compress_exchange(question: str, answer: str, evaluation: str) -> str:
    """Compress a Q&A exchange to a brief gist."""
    # Since we can't reliably call an LLM here without an API key, we will create a simple text summary.
    q_snippet = question[:50] + "..." if len(question) > 50 else question
    a_snippet = answer[:50] + "..." if len(answer) > 50 else answer
    return f"Q: {q_snippet} | A: {a_snippet} | Eval: {evaluation}"

def update_context(session: InterviewSession, question: str, answer: str, evaluation: dict) -> dict:
    """Update compressed context after each turn."""
    context = session.compressed_context or {}
    
    exchanges = context.get('exchanges', [])
    eval_label = evaluation.get('evaluation_label', 'average')
    
    # Add new exchange verbatim
    exchanges.append({
        "question": question,
        "answer": answer,
        "evaluation": eval_label,
        "compressed": False
    })
    
    # Keep last 2 verbatim, compress older ones
    if len(exchanges) > 2:
        for i in range(len(exchanges) - 2):
            if not exchanges[i].get('compressed'):
                exchanges[i]['gist'] = compress_exchange(
                    exchanges[i]['question'],
                    exchanges[i]['answer'],
                    exchanges[i]['evaluation']
                )
                exchanges[i].pop('question', None)
                exchanges[i].pop('answer', None)
                exchanges[i]['compressed'] = True
                
    context['exchanges'] = exchanges
    
    # Update running strengths/weaknesses
    if eval_label == 'strong':
        if 'running_strengths' not in context:
            context['running_strengths'] = []
        context['running_strengths'].append(f"Strong response to: {question[:30]}...")
    elif eval_label in ['weak', 'incorrect']:
        if 'running_weaknesses' not in context:
            context['running_weaknesses'] = []
        context['running_weaknesses'].append(f"Weak response to: {question[:30]}...")
        
    session.compressed_context = context
    return context

def get_stage(session: InterviewSession) -> str:
    """Determine current interview stage based on turn count."""
    turn_count = len(session.turns) if session.turns else 0
    total_target = session.total_questions_target or 10
    
    if turn_count == 0:
        return "introduction"
    
    progress = turn_count / total_target
    
    if progress < 0.3:
        return "resume_discussion"
    elif progress < 0.7:
        return "technical" if session.interview_type == 'technical' else "behavioral"
    elif progress < 0.9:
        return "behavioral"
    else:
        return "closing"
