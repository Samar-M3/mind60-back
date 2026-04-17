from typing import List, Optional

from pydantic import BaseModel, Field


class WellnessAnalyzeRequest(BaseModel):
    """Aggregated client-side wellness signals (browser cannot read other apps natively)."""

    date: str = Field(..., description="Local date YYYY-MM-DD")
    mood: Optional[str] = Field(default=None, description="One of joyful|calm|drained|overwhelmed|wired")
    mind_app_active_minutes: float = Field(ge=0, le=24 * 60)
    mind_app_idle_minutes: float = Field(ge=0, le=24 * 60)
    mind_app_opens: int = Field(ge=0, le=5000)
    midnight_screen_minutes: float = Field(
        ge=0, le=24 * 60, description="Time in MindSathi between 00:00-04:00 local"
    )
    late_night_opens: int = Field(ge=0, le=500, description="Session starts after 23:00 local")
    sleep_hours: Optional[float] = Field(default=None, ge=0, le=24)
    other_screen_hours_estimate: Optional[float] = Field(default=None, ge=0, le=24)
    pickup_estimate: Optional[int] = Field(default=None, ge=0, le=5000)


class WellnessAnalyzeResponse(BaseModel):
    burnout_score: int = Field(ge=0, le=100)
    stress_score: int = Field(ge=0, le=100)
    summary: str
    suggestions: List[str]
    micro_actions: List[str] = Field(default_factory=list)
