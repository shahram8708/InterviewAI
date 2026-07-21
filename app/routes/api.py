"""
JSON API endpoints for the live interview voice loop and speech analysis.
All endpoints return JSON, require login via session, and are CSRF-exempt for fetch calls.
"""
from datetime import datetime, timezone
from flask import Blueprint, request, jsonify, current_app
from app.extensions import db, csrf, limiter
from app.models import User, InterviewSession, InterviewTurn, ResumeProfile
from app.utils.helpers import get_current_user
from app.services.security_service import decrypt_api_key
from app.services.gemini_service import generate_interview_question, evaluate_answer
from app.services.context_service import update_context, get_stage, build_initial_context
from app.services.voice_support import analyze_speech, count_filler_words
from app.services.scoring_service import (generate_scores, detect_skill_gaps,
                                           check_and_award_badges, update_progress_snapshot)

api_bp = Blueprint('api', __name__, url_prefix='/api')
csrf.exempt(api_bp)


@api_bp.before_request
def require_login():
    """Reject unauthenticated requests to all API endpoints."""
    if not get_current_user():
        return jsonify({'error': 'Authentication required. Please log in.'}), 401


def _get_session_or_error(session_id, user):
    """Helper to fetch and validate an interview session belongs to the user."""
    interview_session = InterviewSession.query.get(session_id)
    if not interview_session:
        return None, jsonify({'error': 'Interview session not found.'}), 404
    if interview_session.user_id != user.id:
        return None, jsonify({'error': 'You do not have access to this session.'}), 403
    return interview_session, None, None


@api_bp.route('/interview/<int:session_id>/next-question', methods=['POST'])
@limiter.limit(lambda: current_app.config.get('RATE_LIMIT_API', '60/minute'))
def next_question(session_id):
    """Generate the next interview question for the session."""
    user = get_current_user()
    result = _get_session_or_error(session_id, user)
    interview_session = result[0]
    if result[1]:
        return result[1], result[2]

    if interview_session.status != 'in_progress':
        return jsonify({'error': 'This interview session is no longer active.'}), 400

    try:
        api_key = decrypt_api_key(user.encrypted_api_key)

        # Ensure context exists
        context = interview_session.compressed_context or {}
        if not context:
            resume = ResumeProfile.query.get(interview_session.resume_profile_id)
            context = build_initial_context(resume, interview_session)
            interview_session.compressed_context = context

        # Determine current stage
        stage = get_stage(interview_session)
        interview_session.current_stage = stage

        # Generate question via Gemini
        question_data = generate_interview_question(api_key, context, interview_session)

        # Create the turn record (answer will be filled on submit)
        turn_number = interview_session.turns.count() + 1
        turn = InterviewTurn(
            session_id=session_id,
            sequence_number=turn_number,
            question_text=question_data.get('question', 'Tell me about yourself.'),
            question_category=question_data.get('category', 'role-specific'),
        )
        db.session.add(turn)
        db.session.commit()

        return jsonify({
            'question': turn.question_text,
            'category': turn.question_category,
            'stage': stage,
            'turn_number': turn_number,
            'total_target': interview_session.total_questions_target
        })

    except Exception as e:
        current_app.logger.error(f'Error generating question: {e}')
        return jsonify({'error': 'Failed to generate the next question. Please try again.'}), 500


@api_bp.route('/interview/<int:session_id>/submit-answer', methods=['POST'])
@limiter.limit(lambda: current_app.config.get('RATE_LIMIT_API', '60/minute'))
def submit_answer(session_id):
    """Submit the candidate's answer, evaluate it, and return the AI response."""
    user = get_current_user()
    result = _get_session_or_error(session_id, user)
    interview_session = result[0]
    if result[1]:
        return result[1], result[2]

    data = request.get_json(silent=True) or {}
    answer_text = data.get('answer', '').strip()
    speaking_duration = float(data.get('speaking_duration', 0))

    if not answer_text:
        return jsonify({'error': 'No answer provided.'}), 400

    try:
        api_key = decrypt_api_key(user.encrypted_api_key)

        # Find the most recent turn (the unanswered question)
        latest_turn = InterviewTurn.query.filter_by(session_id=session_id)\
            .order_by(InterviewTurn.sequence_number.desc()).first()

        if not latest_turn:
            return jsonify({'error': 'No question found to answer.'}), 400

        # Analyze speech
        speech_data = analyze_speech(answer_text, speaking_duration)
        filler_counts = speech_data.get('filler_words', {})
        word_count = speech_data.get('word_count', len(answer_text.split()))

        # Evaluate the answer via Gemini
        context = interview_session.compressed_context or {}
        evaluation = evaluate_answer(api_key, context, latest_turn.question_text, answer_text, interview_session)

        # Update the turn record
        latest_turn.answer_text = answer_text
        latest_turn.evaluation_label = evaluation.get('evaluation_label', 'average')
        latest_turn.ai_notes = evaluation.get('ai_notes', '')
        latest_turn.ai_response = evaluation.get('ai_response', '')
        latest_turn.speaking_duration_seconds = speaking_duration
        latest_turn.word_count = word_count
        latest_turn.filler_words_in_turn = filler_counts

        # Update session-level speech metrics
        session_fillers = interview_session.filler_word_counts or {}
        for word, count in filler_counts.items():
            session_fillers[word] = session_fillers.get(word, 0) + count
        interview_session.filler_word_counts = session_fillers
        interview_session.total_words_spoken = (interview_session.total_words_spoken or 0) + word_count
        interview_session.total_speaking_time_seconds = (interview_session.total_speaking_time_seconds or 0) + speaking_duration

        # Update compressed context
        updated_context = update_context(interview_session, latest_turn.question_text, answer_text, evaluation)
        interview_session.compressed_context = updated_context

        # Update stage
        stage = get_stage(interview_session)
        interview_session.current_stage = stage

        # Track question category distribution
        cats = interview_session.question_categories_used or {}
        cat = latest_turn.question_category or 'role-specific'
        cats[cat] = cats.get(cat, 0) + 1
        interview_session.question_categories_used = cats

        db.session.commit()

        turn_count = interview_session.turns.count()
        should_continue = turn_count < interview_session.total_questions_target

        return jsonify({
            'evaluation': evaluation.get('evaluation_label', 'average'),
            'ai_response': evaluation.get('ai_response', 'Thank you for your answer.'),
            'ai_notes': evaluation.get('ai_notes', ''),
            'should_continue': should_continue,
            'category': latest_turn.question_category,
            'stage': stage,
            'turn_number': turn_count,
            'total_target': interview_session.total_questions_target,
            'strengths_so_far': updated_context.get('running_strengths', []),
            'weaknesses_so_far': updated_context.get('running_weaknesses', []),
            'speech_metrics': {
                'wpm': speech_data.get('wpm', 0),
                'filler_words': filler_counts,
                'confidence': speech_data.get('confidence_indicators', {})
            }
        })

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'Error evaluating answer: {e}')
        return jsonify({'error': 'Failed to evaluate your answer. Please try again.'}), 500


@api_bp.route('/interview/<int:session_id>/end', methods=['POST'])
@limiter.limit(lambda: current_app.config.get('RATE_LIMIT_API', '60/minute'))
def end_session(session_id):
    """Finalize the interview session and generate the feedback report."""
    user = get_current_user()
    result = _get_session_or_error(session_id, user)
    interview_session = result[0]
    if result[1]:
        return result[1], result[2]

    try:
        api_key = decrypt_api_key(user.encrypted_api_key)

        # Mark session as completed
        interview_session.status = 'completed'
        interview_session.completed_at = datetime.now(timezone.utc)
        db.session.commit()

        # Get all turns for scoring
        turns = InterviewTurn.query.filter_by(session_id=session_id)\
            .order_by(InterviewTurn.sequence_number).all()

        # Generate comprehensive feedback report
        report = generate_scores(interview_session, turns, api_key)

        # Detect skill gaps from this session
        detect_skill_gaps(user.id, interview_session, report)

        # Check and award any new badges
        check_and_award_badges(user.id)

        # Update weekly progress snapshot
        update_progress_snapshot(user.id)

        return jsonify({
            'status': 'completed',
            'report_url': f'/interview/session/{session_id}/report',
            'overall_score': report.overall_score if report else 0
        })

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'Error finalizing session: {e}')
        return jsonify({'error': 'Failed to generate your feedback report. Please try again.'}), 500


@api_bp.route('/speech/analyze', methods=['POST'])
def analyze_speech_endpoint():
    """Analyze a speech transcript for filler words, WPM, and confidence indicators."""
    data = request.get_json(silent=True) or {}
    text = data.get('text', '')
    duration = float(data.get('duration', 0))

    result = analyze_speech(text, duration)
    return jsonify(result)


@api_bp.route('/interview/<int:session_id>/status', methods=['GET'])
def session_status(session_id):
    """Return the current state of an interview session."""
    user = get_current_user()
    result = _get_session_or_error(session_id, user)
    interview_session = result[0]
    if result[1]:
        return result[1], result[2]

    return jsonify({
        'status': interview_session.status,
        'job_role': interview_session.job_role,
        'company_name': interview_session.company_name,
        'current_stage': interview_session.current_stage,
        'turn_count': interview_session.turns.count(),
        'total_target': interview_session.total_questions_target,
        'started_at': interview_session.started_at.isoformat() if interview_session.started_at else None
    })
