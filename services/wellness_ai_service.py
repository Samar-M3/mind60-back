"""
Burnout / stress insight from wellness signals.
Uses Anthropic when configured; otherwise deterministic heuristics (no network).
"""

import json
import os
from typing import List

try:
    import anthropic  # type: ignore
except Exception:
    anthropic = None

from backend.models.wellness import WellnessAnalyzeRequest, WellnessAnalyzeResponse


def _heuristic_scores(body: WellnessAnalyzeRequest) -> tuple[int, int, str, List[str], List[str]]:
    """Rough scores from usage + sleep + mood — educational, not clinical."""
    burnout = 22
    stress = 25

    active = body.mind_app_active_minutes
    midnight = body.midnight_screen_minutes
    late = body.late_night_opens
    sleep = body.sleep_hours
    other = body.other_screen_hours_estimate or 0.0
    pickup = body.pickup_estimate or 0

    if active > 180:
        burnout += 18
        stress += 12
    elif active > 90:
        burnout += 10
        stress += 6

    if midnight > 25:
        burnout += 14
        stress += 16
    elif midnight > 10:
        burnout += 8
        stress += 10

    late_penalty = min(20, late * 3)
    burnout += late_penalty
    stress += min(18, late * 2)

    if sleep is not None:
        if sleep < 5:
            burnout += 16
            stress += 18
        elif sleep < 6.5:
            burnout += 10
            stress += 10
        elif sleep > 8.5:
            stress -= 4

    if other > 6:
        burnout += 8
        stress += 8
    if pickup > 120:
        stress += 10
    elif pickup > 80:
        stress += 6

    mood = (body.mood or "").lower()
    if mood in ("drained", "overwhelmed", "wired"):
        burnout += 10
        stress += 12
    elif mood == "calm":
        stress -= 6
        burnout -= 4
    elif mood == "joyful":
        stress -= 10
        burnout -= 6

    burnout = int(max(0, min(100, burnout)))
    stress = int(max(0, min(100, stress)))

    summary = (
        f"For {body.date}, your MindSathi active time was about {active:.0f} minutes with "
        f"~{midnight:.0f} minutes after midnight in this app. "
        "This is a gentle mirror, not a diagnosis — patterns often line up with fatigue more than 'weakness'."
    )

    suggestions: List[str] = [
        "Take a 10-minute walk without your phone after your next meal.",
        "Try legs-up-the-wall for 5 minutes before bed to downshift your nervous system.",
        "Schedule a 25-minute focus block, then a 5-minute stretch — repeat twice instead of grinding.",
    ]
    micro_actions: List[str] = [
        "Box breathing: inhale 4s, hold 4s, exhale 4s, hold 4s × 4 rounds.",
        "Drink a full glass of water and roll your shoulders slowly 10 times.",
        "Text one person you trust: 'Can we talk for 10 minutes later?'",
    ]

    if burnout >= 70:
        suggestions.insert(0, "Consider scaling back one non-essential commitment this week.")
    if stress >= 70:
        suggestions.insert(0, "Short grounding audio (3–5 min) can lower perceived stress quickly.")
    if midnight > 15:
        micro_actions.insert(0, "Tonight, try a 'screens down' ritual 45 minutes before you want to sleep.")

    return burnout, stress, summary, suggestions[:5], micro_actions[:5]


async def analyze_wellness(body: WellnessAnalyzeRequest) -> WellnessAnalyzeResponse:
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if api_key and anthropic is not None:
        try:
            client = anthropic.Anthropic(api_key=api_key)
            payload = body.model_dump()
            user_prompt = (
                "You are a supportive wellbeing coach. Given JSON wellness signals from a web app "
                "(only MindSathi time is measured precisely; other screen time is user-estimated), "
                "return STRICT JSON with keys: burnout_score (0-100 int), stress_score (0-100 int), "
                "summary (2-3 sentences, warm tone), suggestions (array of 4-5 short strings: yoga, "
                "meditation, outdoor break, sleep hygiene), micro_actions (array of 3-4 tiny steps). "
                "Scores are educational guesses, not medical. Avoid diagnosing. "
                f"DATA: {json.dumps(payload)}"
            )
            completion = client.messages.create(
                model="claude-3-sonnet-20240229",
                max_tokens=500,
                system="Reply with JSON only. No markdown.",
                messages=[{"role": "user", "content": user_prompt}],
            )
            if completion and completion.content:
                text_parts = [c.text for c in completion.content if hasattr(c, "text")]
                raw = text_parts[0] if text_parts else ""
                start = raw.find("{")
                end = raw.rfind("}")
                if start != -1 and end != -1:
                    data = json.loads(raw[start : end + 1])
                    return WellnessAnalyzeResponse(
                        burnout_score=int(max(0, min(100, int(data.get("burnout_score", 40))))),
                        stress_score=int(max(0, min(100, int(data.get("stress_score", 40))))),
                        summary=str(data.get("summary", "")).strip() or "You are doing your best.",
                        suggestions=list(data.get("suggestions") or [])[:6],
                        micro_actions=list(data.get("micro_actions") or [])[:6],
                    )
        except Exception:
            pass

    b, s, summary, sug, micro = _heuristic_scores(body)
    return WellnessAnalyzeResponse(
        burnout_score=b,
        stress_score=s,
        summary=summary,
        suggestions=sug,
        micro_actions=micro,
    )
