"""Centralised configuration and environment loading."""
from __future__ import annotations

import os
from pathlib import Path
from dotenv import load_dotenv

ROOT_DIR = Path(__file__).resolve().parent.parent
load_dotenv(ROOT_DIR / '.env')

MONGO_URL = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
DB_NAME = os.environ.get('DB_NAME', 'sftc_database')

JWT_SECRET = os.environ.get('JWT_SECRET', 'sftc-dev-secret')
JWT_ALGORITHM = 'HS256'
ACCESS_TOKEN_EXPIRE_DAYS = 30

EMERGENT_LLM_KEY = os.environ.get('EMERGENT_LLM_KEY')
OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY') or os.environ.get('EXPO_PUBLIC_VIBECODE_OPENAI_API_KEY')
OPENAI_BASE_URL = os.environ.get('OPENAI_BASE_URL')

AI_WORKOUT_MODEL = os.environ.get('AI_WORKOUT_MODEL', 'claude-sonnet-4-5-20250929')
AI_COACH_MODEL = os.environ.get('AI_COACH_MODEL', 'claude-sonnet-4-5-20250929')
AI_MEAL_MODEL = os.environ.get('AI_MEAL_MODEL', 'claude-sonnet-4-5-20250929')
AI_JOURNAL_MODEL = os.environ.get('AI_JOURNAL_MODEL', 'claude-sonnet-4-5-20250929')

# legacy openai meal model (used only as fallback)
LEGACY_OPENAI_MODEL = os.environ.get('MEAL_AI_MODEL', 'gpt-4o-mini')

# Territory tuning
H3_RESOLUTION = int(os.environ.get('H3_RESOLUTION', '9'))  # ~174m hex edge
RUN_MIN_POINTS = 5
RUN_MIN_DURATION_SEC = 60
RUN_MIN_DISTANCE_KM = 0.2
RUN_MAX_SPEED_MPS = 8.0      # ~28.8 km/h running ceiling
RUN_TELEPORT_SPEED_MPS = 30.0  # any single segment above this = teleport
TREK_MAX_SPEED_MPS = 5.0
PEAK_MIN_ELEVATION_GAIN_M = 50.0
