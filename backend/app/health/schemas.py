from datetime import date
from pydantic import BaseModel, Field


class CheckInCommand(BaseModel):
    local_date: date
    sleep_minutes: int | None = Field(default=None, ge=0, le=1440)
    sleep_quality: int | None = Field(default=None, ge=1, le=5)
    mood: int | None = Field(default=None, ge=1, le=5)
    stress: int | None = Field(default=None, ge=1, le=5)
    readiness: int | None = Field(default=None, ge=1, le=5)


class PainCommand(BaseModel):
    region_code: str
    severity: int = Field(ge=0, le=10)
    during_activity: bool
    description: str = Field(max_length=2000)


def conservative_action(command: PainCommand) -> str:
    if command.severity >= 8: return "stop_and_seek_urgent_assessment"
    if command.severity >= 5 or command.during_activity: return "stop_and_seek_professional_assessment"
    if command.severity > 0: return "modify_and_monitor"
    return "no_pain_reported"

