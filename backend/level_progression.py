from __future__ import annotations

import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional


LEVELS = ["beginner", "intermediate", "advanced"]


def _level_index(level: str) -> int:
    normalized = str(level or "intermediate").lower()
    return LEVELS.index(normalized) if normalized in LEVELS else 1


def _normalize_level(level: Any) -> str:
    normalized = str(level or "intermediate").lower().strip()
    return normalized if normalized in LEVELS else "intermediate"


def _next_level(level: str) -> str:
    return LEVELS[min(len(LEVELS) - 1, _level_index(level) + 1)]


def _previous_level(level: str) -> str:
    return LEVELS[max(0, _level_index(level) - 1)]


def _feedback_intensity(workout: Dict[str, Any]) -> Optional[float]:
    feedback = workout.get("user_feedback") or {}
    value = feedback.get("rpe") if feedback.get("rpe") is not None else feedback.get("intensity_rating")
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


async def compute_user_level_assessment(
    db: Any,
    *,
    user_id: str,
    profile: Dict[str, Any],
    persist: bool = True,
) -> Dict[str, Any]:
    """Compute objective level recommendation while leaving final review visible to the product/user."""
    now = datetime.utcnow()
    window_start = now - timedelta(days=120)
    current_level = _normalize_level(profile.get("experience") or profile.get("fitness_level"))

    workouts = await db.workouts.find({
        "user_id": user_id,
        "created_at": {"$gte": window_start},
    }).to_list(300)
    completed_workouts = [workout for workout in workouts if workout.get("completed")]
    planned_count = len(workouts)
    completed_count = len(completed_workouts)
    completion_rate = (completed_count / planned_count) if planned_count else 0

    intensities = [value for workout in completed_workouts if (value := _feedback_intensity(workout)) is not None]
    avg_intensity = round(sum(intensities) / len(intensities), 2) if intensities else None

    active_injuries = await db.injuries.find({"user_id": user_id, "is_active": True}).to_list(50)
    recent_injury_logs = await db.injury_logs.find({
        "user_id": user_id,
        "logged_at": {"$gte": window_start},
    }).sort("logged_at", -1).to_list(50)
    recent_pain_scores = [
        int(log.get("pain_scale"))
        for log in recent_injury_logs
        if isinstance(log.get("pain_scale"), int)
    ]
    pain_risk = bool(active_injuries) or any(score >= 4 for score in recent_pain_scores[:5])

    history = await db.user_exercise_history.find({
        "user_id": user_id,
        "date": {"$gte": window_start.strftime("%Y-%m-%d")},
    }).to_list(500)
    painful_history = [
        item for item in history
        if isinstance(item.get("pain_score"), (int, float)) and item.get("pain_score") >= 4
    ]
    if painful_history:
        pain_risk = True

    evidence: Dict[str, Any] = {
        "window_days": 120,
        "planned_workouts": planned_count,
        "completed_workouts": completed_count,
        "completion_rate": round(completion_rate, 3),
        "average_intensity_rating": avg_intensity,
        "active_injury_count": len(active_injuries),
        "recent_high_pain_entries": len(painful_history),
        "exercise_history_entries": len(history),
    }

    reasons: List[str] = []
    recommendation_type = "hold"
    recommended_level = current_level

    if planned_count >= 4 and completion_rate < 0.65:
        recommendation_type = "regress_or_hold"
        recommended_level = _previous_level(current_level)
        reasons.append("Completion rate is below 65%, so progression should pause or regress.")
    elif pain_risk:
        recommendation_type = "hold"
        recommended_level = current_level
        reasons.append("Pain or active injury signals are present, so level should not increase.")
    elif current_level == "beginner" and completed_count >= 8 and completion_rate >= 0.85:
        recommendation_type = "upgrade"
        recommended_level = "intermediate"
        reasons.append("Beginner has completed at least 8 workouts with 85%+ completion and no pain risk.")
    elif current_level == "intermediate" and completed_count >= 16 and completion_rate >= 0.85:
        recommendation_type = "upgrade"
        recommended_level = "advanced"
        reasons.append("Intermediate has completed at least 16 workouts with 85%+ completion and no pain risk.")
    else:
        reasons.append("Keep current level until more consistent completion and recovery data is available.")

    if avg_intensity is not None and avg_intensity >= 9 and recommendation_type == "upgrade":
        recommendation_type = "hold"
        recommended_level = current_level
        reasons.append("Average intensity is very high, so avoid upgrading until sessions feel more controlled.")

    assessment = {
        "id": str(uuid.uuid4()),
        "user_id": user_id,
        "created_at": now,
        "status": "pending_review",
        "current_level": current_level,
        "recommended_level": recommended_level,
        "recommendation_type": recommendation_type,
        "review_mode": "auto_with_review",
        "evidence": evidence,
        "reasons": reasons,
    }

    if persist:
        await db.user_level_assessments.insert_one(assessment)
    return assessment
