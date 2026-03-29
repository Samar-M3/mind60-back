"""
Abstractions over Firestore reads/writes plus helper utilities
like anonymous alias generation.
"""

import random
from datetime import datetime, timezone
from typing import Dict, List, Literal, Optional

from backend.core.firebase import get_db

# Simple word lists for anonymous alias generation
ADJECTIVES = [
    "Calm",
    "Quiet",
    "Gentle",
    "Brave",
    "Kind",
    "Steady",
    "Bright",
    "Soft",
    "Hopeful",
    "Patient",
    "Warm",
    "Luminous",
]

NATURE_NOUNS = [
    "River",
    "Moon",
    "Forest",
    "Horizon",
    "Breeze",
    "Summit",
    "Harbor",
    "Lagoon",
    "Valley",
    "Dawn",
    "Garden",
    "Meadow",
]


def generate_alias(seed: Optional[int] = None) -> str:
    rng = random.Random(seed)
    adjective = rng.choice(ADJECTIVES)
    noun = rng.choice(NATURE_NOUNS)
    suffix = rng.randint(7, 99)
    return f"{adjective}{noun}{suffix}"


def get_user_profile(uid: str) -> Optional[Dict]:
    db = get_db()
    doc = db.collection("users").document(uid).get()
    if not doc.exists:
        return None
    return doc.to_dict()


def ensure_user_profile(uid: str, email: Optional[str], default_role: str = "user"):
    """
    Create a minimal user profile if it doesn't exist yet,
    ensuring every user receives a stable anonymous alias.
    """
    db = get_db()
    doc_ref = db.collection("users").document(uid)
    snap = doc_ref.get()

    if snap.exists:
        data = snap.to_dict()
        # Backfill alias if missing
        updates = {}
        if not data.get("alias"):
            data["alias"] = generate_alias(int(uid[-6:], 16) if len(uid) >= 6 else None)
            updates["alias"] = data["alias"]
        if not data.get("createdAt"):
            data["createdAt"] = datetime.now(timezone.utc).isoformat()
            updates["createdAt"] = data["createdAt"]
        if not data.get("role"):
            data["role"] = "user"
            updates["role"] = "user"
        if updates:
            doc_ref.update(updates)
        return data

    alias = generate_alias(int(uid[-6:], 16) if len(uid) >= 6 else None)
    created_at = datetime.now(timezone.utc).isoformat()
    profile = {
        "uid": uid,
        "email": email,
        "role": "user" if default_role not in {"user"} else default_role,
        "alias": alias,
        "createdAt": created_at,
    }
    doc_ref.set(profile)
    return profile


def save_mood_entry(uid: str, mood: int):
    """Store a daily mood entry for the user."""
    db = get_db()
    entry = {
        "value": mood,
        "createdAt": datetime.now(timezone.utc).isoformat(),
    }
    db.collection("users").document(uid).collection("moods").add(entry)
    return entry


def get_mood_history(uid: str, limit: int = 30):
    """Fetch recent mood entries (default last 30)."""
    db = get_db()
    entries = []
    moods_ref = (
        db.collection("users")
        .document(uid)
        .collection("moods")
        .order_by("createdAt", direction="DESCENDING")
        .limit(limit)
    )
    for doc in moods_ref.stream():
        entries.append(doc.to_dict())
    return entries[::-1]  # return chronological


def save_game_score(game_id: str, uid: str, alias: str, score: int) -> Dict:
    """Store a user's best score for a mini-game."""
    db = get_db()
    score_ref = (
        db.collection("game_leaderboards")
        .document(game_id)
        .collection("scores")
        .document(uid)
    )
    snap = score_ref.get()
    now = datetime.now(timezone.utc).isoformat()

    previous_best = -1
    if snap.exists:
        previous_best = int(snap.to_dict().get("score", -1))

    best_score = max(previous_best, score)
    payload = {
        "uid": uid,
        "alias": alias,
        "gameId": game_id,
        "score": best_score,
        "updatedAt": now,
    }
    score_ref.set(payload)

    return {
        "gameId": game_id,
        "score": score,
        "bestScore": best_score,
        "isPersonalBest": score >= previous_best,
        "updatedAt": now,
    }


def get_game_leaderboard(game_id: str, current_uid: str, limit: int = 10) -> List[Dict]:
    """Return the top leaderboard entries for the requested game."""
    db = get_db()
    entries: List[Dict] = []
    docs = (
        db.collection("game_leaderboards")
        .document(game_id)
        .collection("scores")
        .order_by("score", direction="DESCENDING")
        .limit(limit)
        .stream()
    )

    for doc in docs:
        data = doc.to_dict()
        data["isCurrentUser"] = data.get("uid") == current_uid
        entries.append(data)

    return entries


def list_pending_role_requests(limit: int = 100) -> List[Dict]:
    """Return users who requested a professional role but are not approved yet."""
    db = get_db()
    pending: List[Dict] = []
    docs = (
        db.collection("users")
        .where("role", "==", "user")
        .limit(limit)
        .stream()
    )
    for doc in docs:
        data = doc.to_dict()
        requested_role = data.get("requestedRole")
        if requested_role in {"doctor", "therapist", "psychiatrist"}:
            pending.append(data)
    return pending


def approve_role_request(
    uid: str,
    approved_role: Literal["doctor", "therapist", "psychiatrist"],
) -> Dict:
    """Approve a previously requested professional role."""
    db = get_db()
    doc_ref = db.collection("users").document(uid)
    snap = doc_ref.get()
    if not snap.exists:
        raise ValueError("User not found")

    data = snap.to_dict()
    requested_role = data.get("requestedRole")
    if requested_role not in {"doctor", "therapist", "psychiatrist"}:
        raise ValueError("No pending professional role request")

    updated_at = datetime.now(timezone.utc).isoformat()
    updates = {
        "role": approved_role,
        "requestedRole": approved_role,
        "updatedAt": updated_at,
    }
    doc_ref.update(updates)
    return {
        "uid": uid,
        "role": approved_role,
        "requestedRole": approved_role,
        "updatedAt": updated_at,
    }


def reject_role_request(uid: str) -> Dict:
    """Reject a requested professional role and keep the user at the basic role."""
    db = get_db()
    doc_ref = db.collection("users").document(uid)
    snap = doc_ref.get()
    if not snap.exists:
        raise ValueError("User not found")

    data = snap.to_dict()
    requested_role = data.get("requestedRole")
    if requested_role not in {"doctor", "therapist", "psychiatrist"}:
        raise ValueError("No pending professional role request")

    updated_at = datetime.now(timezone.utc).isoformat()
    doc_ref.update(
        {
            "role": "user",
            "requestedRole": None,
            "updatedAt": updated_at,
        }
    )
    return {
        "uid": uid,
        "role": "user",
        "requestedRole": None,
        "updatedAt": updated_at,
    }

