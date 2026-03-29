from fastapi import APIRouter, Depends
from backend.core.security import get_current_user
from backend.models import UserProfile
from backend.services.firestore_service import ensure_user_profile

router = APIRouter(prefix="/auth", tags=["auth"])


@router.get("/me", response_model=UserProfile)
async def get_me(current_user=Depends(get_current_user)):
    """
    Return the current user's profile (including anonymous alias).
    Ensures a profile document exists in Firestore.
    """
    profile = ensure_user_profile(
        uid=current_user["uid"],
        email=current_user.get("email"),
        default_role=current_user.get("role", "user"),
    )
    return UserProfile(**profile)

