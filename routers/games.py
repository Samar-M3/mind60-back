from fastapi import APIRouter, Depends, HTTPException

from backend.core.security import get_current_user
from backend.models.game import (
    GameLeaderboardResponse,
    GameScoreResponse,
    GameScoreSubmit,
)
from backend.services.firestore_service import (
    ensure_user_profile,
    get_game_leaderboard,
    save_game_score,
)

router = APIRouter(prefix="/games", tags=["games"])

SUPPORTED_GAMES = {"visual-memory"}


def validate_game_id(game_id: str) -> str:
    if game_id not in SUPPORTED_GAMES:
        raise HTTPException(status_code=404, detail="Game not found")
    return game_id


@router.get("/{game_id}/leaderboard", response_model=GameLeaderboardResponse)
async def leaderboard(
    game_id: str,
    limit: int = 10,
    current_user=Depends(get_current_user),
):
    game_id = validate_game_id(game_id)
    entries = get_game_leaderboard(
        game_id=game_id,
        current_uid=current_user["uid"],
        limit=max(1, min(limit, 25)),
    )
    return GameLeaderboardResponse(gameId=game_id, entries=entries)


@router.post("/{game_id}/score", response_model=GameScoreResponse)
async def submit_score(
    game_id: str,
    body: GameScoreSubmit,
    current_user=Depends(get_current_user),
):
    game_id = validate_game_id(game_id)
    profile = ensure_user_profile(
        uid=current_user["uid"],
        email=current_user.get("email"),
        default_role=current_user.get("role", "user"),
    )
    result = save_game_score(
        game_id=game_id,
        uid=current_user["uid"],
        alias=profile.get("alias", "Mind Friend"),
        score=body.score,
    )
    return GameScoreResponse(**result)
