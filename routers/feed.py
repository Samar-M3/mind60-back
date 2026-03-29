from typing import List
from fastapi import APIRouter, Depends

from backend.core.security import get_current_user
from backend.models import PostResponse
from backend.services.feed_algorithm import rank_posts
from backend.core.firebase import get_db

router = APIRouter(prefix="/feed", tags=["feed"])


@router.get("", response_model=List[PostResponse])
async def get_ranked_feed(limit: int = 20, current_user=Depends(get_current_user)):
    """
    Return posts ranked by AI-inspired feed algorithm.
    """
    db = get_db()
    posts = []
    for doc in (
        db.collection("posts")
        .order_by("createdAt", direction="DESCENDING")
        .limit(limit)
        .stream()
    ):
        posts.append(doc.to_dict())

    # Minimal personalization stub
    user_context = {
        "preferred_tags": [],  # could be derived from user history later
    }

    ranked = rank_posts(posts, user_context=user_context)
    return [PostResponse(**p, userReaction=None) for p in ranked]
