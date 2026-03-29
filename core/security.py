"""
Security helpers: token verification dependency and role checks.
"""
from fastapi import Depends, Header, HTTPException, status

from backend.core.firebase import verify_id_token
from backend.core.config import settings


async def get_current_user(authorization: str = Header(None)):
    """
    FastAPI dependency that validates the Firebase bearer token
    and returns the decoded claims.
    """
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing Authorization: Bearer <token>",
        )

    token = authorization.split(" ", 1)[1]
    try:
        decoded = verify_id_token(token)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )
    return decoded


def assert_professional_role(user_role: str):
    """Raise 403 if the role is not one of the professional roles."""
    if user_role not in {"doctor", "therapist", "psychiatrist"}:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only verified professionals can perform this action",
        )


def assert_admin_user(current_user: dict):
    """Raise 403 unless the current UID is allowlisted as an admin."""
    if current_user.get("uid") not in set(settings.admin_uids):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )

