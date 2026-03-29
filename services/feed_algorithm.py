"""
AI-inspired scoring for ranking feed posts.
Weighted factors: recency, engagement, distress priority, personalization.
"""

from datetime import datetime, timezone
from typing import Dict, List


def _parse_iso(ts: str) -> datetime:
    try:
        return datetime.fromisoformat(ts.replace("Z", "+00:00")).astimezone(timezone.utc)
    except Exception:
        return datetime.now(timezone.utc)


def _hours_since(ts: str) -> float:
    return (datetime.now(timezone.utc) - _parse_iso(ts)).total_seconds() / 3600


def calculate_score(post: Dict, user_context: Dict | None = None) -> float:
    user_context = user_context or {}

    # Recency: decay after 24h
    hours = _hours_since(post.get("createdAt", datetime.now(timezone.utc).isoformat()))
    recency_score = max(0.0, 1.0 - (hours / 48.0))  # 0..1

    # Engagement: reactions and comments
    rc = post.get("reactionCounts", {}) or {}
    reactions_total = sum(rc.values())
    comments = post.get("commentCount", 0)
    engagement_score = min(1.0, (reactions_total * 1.5 + comments * 2) / 30)

    # Distress priority: gently boost high/critical
    distress = post.get("distress") or {}
    distress_level = distress.get("level")
    distress_score = {"critical": 1.0, "high": 0.8, "medium": 0.4, "low": 0.1}.get(
        distress_level, 0
    )

    # Personalization (mock): match on moodTag preference list
    preferred = set(user_context.get("preferred_tags", []))
    mood_tag = post.get("moodTag")
    personalization_score = 0.2 if mood_tag and mood_tag in preferred else 0.0

    # Weighted sum
    return (
        recency_score * 0.4
        + engagement_score * 0.3
        + distress_score * 0.2
        + personalization_score * 0.1
    )


def rank_posts(posts: List[Dict], user_context: Dict | None = None) -> List[Dict]:
    for post in posts:
        post["feed_score"] = calculate_score(post, user_context)
    return sorted(posts, key=lambda p: p.get("feed_score", 0), reverse=True)

