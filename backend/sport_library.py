"""Sport library: per-sport section structure + adapters over the knowledge base.

Pure config/transforms — no DB access. The section layout per sport follows the
family blueprints in docs/SPORT_CONTENT_RESEARCH.md. Knowledge-base docs
(sport_teaching_progressions, sport_skill_assessments) are adapted into typed
units; generated content (rules, tactics, technique articles) lands in these
same sections later.
"""
from typing import Any, Dict, List, Optional

# Onboarding sport names -> knowledge-base sport keys.
ONBOARDING_TO_KB: Dict[str, str] = {
    'Badminton': 'badminton',
    'Basketball': 'basketball',
    'Boxing': 'boxing',
    'Cricket': 'cricket',
    'Cycling': 'cycling',
    'Football': 'soccer',
    'Golf': 'golf',
    'Hockey': 'hockey',
    'Horse Riding': 'horse_riding',
    'Hyrox': 'hyrox',
    'MMA': 'mma',
    'Rugby': 'rugby',
    'Running': 'running_endurance',
    'Swimming': 'swimming',
    'Table Tennis': 'table_tennis',
    'Tennis': 'tennis',
    'Volleyball': 'volleyball',
}

# Section layouts per family. `kb` marks the section that receives the
# knowledge base's teaching progressions (drills). Every sport ends with a
# Progression section fed by skill assessments — LTAD applies to all sports.
_ENDURANCE = [
    {'id': 'technique', 'title': 'Technique', 'icon': 'body-outline', 'kb': True},
    {'id': 'training', 'title': 'Training', 'icon': 'trending-up-outline'},
    {'id': 'racing', 'title': 'Racing', 'icon': 'flag-outline'},
    {'id': 'rules', 'title': 'Rules & formats', 'icon': 'book-outline'},
]
_RACKET = [
    {'id': 'fundamentals', 'title': 'Fundamentals', 'icon': 'body-outline', 'kb': True},
    {'id': 'shots', 'title': 'Shots', 'icon': 'tennisball-outline'},
    {'id': 'tactics', 'title': 'Tactics', 'icon': 'bulb-outline'},
    {'id': 'rules', 'title': 'Rules & scoring', 'icon': 'book-outline'},
]
_INVASION = [
    {'id': 'game', 'title': 'The game', 'icon': 'information-circle-outline'},
    {'id': 'skills', 'title': 'Skills', 'icon': 'body-outline', 'kb': True},
    {'id': 'tactics', 'title': 'Tactics', 'icon': 'git-network-outline'},
    {'id': 'iq', 'title': 'Game IQ', 'icon': 'bulb-outline'},
    {'id': 'rules', 'title': 'Rules', 'icon': 'book-outline'},
]
_COMBAT = [
    {'id': 'fundamentals', 'title': 'Fundamentals', 'icon': 'body-outline', 'kb': True},
    {'id': 'offense', 'title': 'Offense', 'icon': 'flash-outline'},
    {'id': 'defense', 'title': 'Defense', 'icon': 'shield-outline'},
    {'id': 'iq', 'title': 'Fight IQ', 'icon': 'bulb-outline'},
    {'id': 'rules', 'title': 'Rules & safety', 'icon': 'book-outline'},
]
_CRICKET = [
    {'id': 'game', 'title': 'The game & formats', 'icon': 'information-circle-outline'},
    {'id': 'batting', 'title': 'Batting', 'icon': 'body-outline', 'kb': True},
    {'id': 'bowling', 'title': 'Bowling', 'icon': 'baseball-outline'},
    {'id': 'fielding', 'title': 'Fielding & keeping', 'icon': 'hand-left-outline'},
    {'id': 'tactics', 'title': 'Tactics', 'icon': 'bulb-outline'},
    {'id': 'rules', 'title': 'Laws', 'icon': 'book-outline'},
]
_GOLF = [
    {'id': 'fundamentals', 'title': 'Fundamentals', 'icon': 'body-outline', 'kb': True},
    {'id': 'swing', 'title': 'Full swing', 'icon': 'golf-outline'},
    {'id': 'short_game', 'title': 'Short game', 'icon': 'locate-outline'},
    {'id': 'course', 'title': 'Course management', 'icon': 'bulb-outline'},
    {'id': 'rules', 'title': 'Rules & etiquette', 'icon': 'book-outline'},
]
_HYROX = [
    {'id': 'format', 'title': 'The format', 'icon': 'information-circle-outline'},
    {'id': 'stations', 'title': 'Station technique', 'icon': 'body-outline', 'kb': True},
    {'id': 'strategy', 'title': 'Race strategy', 'icon': 'bulb-outline'},
    {'id': 'training', 'title': 'Training', 'icon': 'trending-up-outline'},
]
_EQUESTRIAN = [
    {'id': 'foundations', 'title': 'Foundations & safety', 'icon': 'shield-outline', 'kb': True},
    {'id': 'gaits', 'title': 'The gaits', 'icon': 'body-outline'},
    {'id': 'disciplines', 'title': 'Disciplines', 'icon': 'ribbon-outline'},
    {'id': 'care', 'title': 'Horse care', 'icon': 'heart-outline'},
    {'id': 'rules', 'title': 'Rules & competition', 'icon': 'book-outline'},
]

SPORT_SECTIONS: Dict[str, List[Dict[str, Any]]] = {
    'running_endurance': _ENDURANCE,
    'swimming': _ENDURANCE,
    'cycling': _ENDURANCE,
    'tennis': _RACKET,
    'badminton': _RACKET,
    'table_tennis': _RACKET,
    'volleyball': _RACKET,
    'basketball': _INVASION,
    'soccer': _INVASION,
    'hockey': _INVASION,
    'rugby': _INVASION,
    'boxing': _COMBAT,
    'mma': _COMBAT,
    'cricket': _CRICKET,
    'golf': _GOLF,
    'hyrox': _HYROX,
    'horse_riding': _EQUESTRIAN,
}

PROGRESSION_SECTION = {'id': 'progression', 'title': 'Progression', 'icon': 'stairs-outline'}


def sections_for(kb_key: str) -> List[Dict[str, Any]]:
    base = SPORT_SECTIONS.get(kb_key, _ENDURANCE)
    return [dict(s) for s in base] + [dict(PROGRESSION_SECTION)]


def kb_section_id(kb_key: str) -> str:
    for s in SPORT_SECTIONS.get(kb_key, _ENDURANCE):
        if s.get('kb'):
            return s['id']
    return 'technique'


def _humanize(value: str) -> str:
    return (value or '').replace('_', ' ').strip().capitalize()


def drill_unit_summary(doc: Dict[str, Any]) -> Dict[str, Any]:
    return {
        'id': doc.get('id'),
        'type': 'drill',
        'title': _humanize(doc.get('domain', 'practice')),
        'level': doc.get('level') or 'beginner',
        'domain': doc.get('domain'),
    }


def drill_unit_detail(doc: Dict[str, Any]) -> Dict[str, Any]:
    return {
        **drill_unit_summary(doc),
        'goal': doc.get('learning_goal'),
        'prerequisites': doc.get('prerequisites') or [],
        'focus': doc.get('technical_focus') or [],
        'priorities': doc.get('teaching_priorities') or [],
        'drills': doc.get('typical_drills') or doc.get('practice_design') or [],
        'avoid': doc.get('avoid_until_ready') or [],
    }


def progression_unit_summary(doc: Dict[str, Any]) -> Dict[str, Any]:
    return {
        'id': doc.get('id'),
        'type': 'progression',
        'title': f"{_humanize(doc.get('domain', 'skills'))} checkpoints",
        'level': 'all',
        'domain': doc.get('domain'),
    }


def progression_unit_detail(doc: Dict[str, Any]) -> Dict[str, Any]:
    bands = []
    for band in doc.get('level_bands') or []:
        bands.append({
            'level': band.get('level'),
            'indicators': band.get('indicators') or [],
            'ready_when': band.get('ready_for_next_when') or [],
        })
    return {
        **progression_unit_summary(doc),
        'summary': doc.get('summary'),
        'metrics': doc.get('metrics') or [],
        'bands': bands,
    }
