"""
Badge catalog — the single source of truth for achievement definitions.

Each definition owns its unlock condition and (where the milestone is countable) the
formula for progress toward it. Both the awarding pipeline
(`scoring_service.check_and_award_badges`) and the achievements page read from this
catalog, so an achievement can never be described one way and awarded another.

Conditions are pure functions of the statistics dictionary produced by
`analytics_service.get_user_statistics`, which is derived entirely from the
authenticated user's own database records.
"""
from dataclasses import dataclass
from typing import Callable, Optional


@dataclass(frozen=True)
class BadgeDefinition:
    """An achievement rule evaluated against real user statistics."""
    badge_type: str
    name: str
    description: str
    icon: str
    condition: Callable[[dict], bool]
    progress: Optional[Callable[[dict], tuple]] = None

    def is_earned(self, stats: dict) -> bool:
        """Return True when the user's real statistics satisfy this achievement."""
        return bool(self.condition(stats))

    def get_progress(self, stats: dict) -> Optional[tuple]:
        """Return (current, target) toward this achievement, or None when not countable."""
        if self.progress is None:
            return None
        current, target = self.progress(stats)
        return min(current, target), target


# Minimum spoken words a session must contain before its filler-word rate is treated as
# meaningful. Without it, a session with no measured speech would trivially unlock the
# "few filler words" achievement.
MIN_WORDS_FOR_FLUENCY_BADGE = 50

# Words-per-minute window considered a well-paced delivery.
IDEAL_WPM_RANGE = (140, 160)

BADGE_DEFINITIONS = (
    BadgeDefinition(
        badge_type='first_interview',
        name='First Steps',
        description='Complete your first interview',
        icon='🎯',
        condition=lambda s: s['completed_sessions'] >= 1,
        progress=lambda s: (s['completed_sessions'], 1),
    ),
    BadgeDefinition(
        badge_type='five_interviews',
        name='High Five',
        description='Complete 5 interviews',
        icon='🖐️',
        condition=lambda s: s['completed_sessions'] >= 5,
        progress=lambda s: (s['completed_sessions'], 5),
    ),
    BadgeDefinition(
        badge_type='ten_interviews',
        name='Perfect Ten',
        description='Complete 10 interviews',
        icon='🔟',
        condition=lambda s: s['completed_sessions'] >= 10,
        progress=lambda s: (s['completed_sessions'], 10),
    ),
    BadgeDefinition(
        badge_type='perfect_score',
        name='Perfectionist',
        description='Score 95 or above in an interview',
        icon='⭐',
        condition=lambda s: s['best_score'] >= 95,
        progress=lambda s: (int(s['best_score']), 95),
    ),
    BadgeDefinition(
        badge_type='streak_3',
        name='On Fire',
        description='Practise 3 days in a row',
        icon='🔥',
        condition=lambda s: s['longest_streak'] >= 3,
        progress=lambda s: (s['longest_streak'], 3),
    ),
    BadgeDefinition(
        badge_type='streak_7',
        name='Unstoppable',
        description='Practise 7 days in a row',
        icon='🚀',
        condition=lambda s: s['longest_streak'] >= 7,
        progress=lambda s: (s['longest_streak'], 7),
    ),
    BadgeDefinition(
        badge_type='speed_demon',
        name='Paced Perfectly',
        description=f'Deliver an interview at {IDEAL_WPM_RANGE[0]}-{IDEAL_WPM_RANGE[1]} words per minute',
        icon='⏱️',
        condition=lambda s: s['has_ideal_pace_session'],
    ),
    BadgeDefinition(
        badge_type='smooth_talker',
        name='Smooth Talker',
        description='Complete an interview with almost no filler words',
        icon='🗣️',
        condition=lambda s: s['has_low_filler_session'],
    ),
    BadgeDefinition(
        badge_type='company_expert',
        name='Company Expert',
        description='Complete 3 interviews for the same company',
        icon='🏢',
        condition=lambda s: s['max_sessions_single_company'] >= 3,
        progress=lambda s: (s['max_sessions_single_company'], 3),
    ),
)

BADGE_DEFINITIONS_BY_TYPE = {definition.badge_type: definition for definition in BADGE_DEFINITIONS}

TOTAL_BADGE_COUNT = len(BADGE_DEFINITIONS)
