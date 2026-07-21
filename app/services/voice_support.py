"""
Voice and speech analysis support.
"""
import re
import logging

logger = logging.getLogger(__name__)

FILLER_WORDS = [
    "umm", "uhh", "ahh", "like", "basically", "you know",
    "sort of", "kind of", "i mean", "actually", "literally", "right"
]

def count_filler_words(text: str) -> dict:
    """Count occurrences of specific filler words in text."""
    if not text:
        return {}
        
    text_lower = text.lower()
    counts = {}
    
    for filler in FILLER_WORDS:
        # Use regex to find whole word matches
        pattern = r'\b' + re.escape(filler) + r'\b'
        matches = re.findall(pattern, text_lower)
        if matches:
            counts[filler] = len(matches)
            
    return counts

def calculate_wpm(word_count: int, duration_seconds: float) -> int:
    """Calculate words per minute."""
    if duration_seconds <= 0 or word_count <= 0:
        return 0
    
    minutes = duration_seconds / 60.0
    return int(round(word_count / minutes))

def analyze_speech(text: str, duration_seconds: float) -> dict:
    """Combined analysis returning filler_words, wpm, word_count, confidence_indicators."""
    if not text:
        return {
            'filler_words': {},
            'wpm': 0,
            'word_count': 0,
            'confidence_indicators': {
                'has_hesitation': False,
                'fluent_delivery': False
            }
        }
        
    words = [w for w in re.split(r'\s+', text) if w]
    word_count = len(words)
    
    fillers = count_filler_words(text)
    total_fillers = sum(fillers.values())
    wpm = calculate_wpm(word_count, duration_seconds)
    
    # Simple confidence indicators
    filler_rate = total_fillers / word_count if word_count > 0 else 0
    fluent_delivery = (wpm >= 120 and wpm <= 160) and filler_rate < 0.05
    has_hesitation = filler_rate > 0.1 or wpm < 100
    
    return {
        'filler_words': fillers,
        'wpm': wpm,
        'word_count': word_count,
        'confidence_indicators': {
            'has_hesitation': has_hesitation,
            'fluent_delivery': fluent_delivery
        }
    }
