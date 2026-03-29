"""
Lightweight AI helpers. For MVP we use keyword-based distress scoring.
Can be swapped with real LLM/transformer models later.
"""

from typing import Dict, Literal


DistressLevel = Literal["low", "medium", "high", "critical"]


KEYWORDS = {
    "critical": ["suicide", "end it", "cant go on", "can't go on", "hopeless"],
    "high": ["depressed", "alone", "crying", "panic", "worthless", "anxious attack"],
    "medium": ["anxious", "stressed", "overwhelmed", "tired", "worried"],
    "low": ["sad", "upset", "meh"],
}


def analyze_distress(text: str) -> Dict:
    """Return a mock distress score based on keyword presence."""
    lower_text = text.lower()
    level: DistressLevel = "low"
    score = 15

    for candidate_level, words in KEYWORDS.items():
        if any(word in lower_text for word in words):
            level = candidate_level  # type: ignore
            break

    level_to_score = {"low": 20, "medium": 55, "high": 75, "critical": 90}
    score = level_to_score.get(level, 20)

    return {"score": score, "level": level}

