from datetime import datetime, timezone
import uuid
from typing import List

from fastapi import APIRouter, Depends, HTTPException

from backend.core.security import get_current_user
from backend.models import PostCreate, PostResponse
from backend.services.ai_service import analyze_distress
from backend.services.firestore_service import ensure_user_profile
from backend.core.firebase import get_db

router = APIRouter(prefix="/posts", tags=["posts"])


@router.post("", response_model=PostResponse)
async def create_post(body: PostCreate, current_user=Depends(get_current_user)):
    if not body.content.strip():
        raise HTTPException(status_code=400, detail="Content cannot be empty")

    db = get_db()
    profile = ensure_user_profile(
        uid=current_user["uid"],
        email=current_user.get("email"),
        default_role=current_user.get("role", "user"),
    )

    distress = analyze_distress(body.content)
    post_id = str(uuid.uuid4())
    created_at = datetime.now(timezone.utc).isoformat()

    post_record = {
        "id": post_id,
        "content": body.content,
        "userId": current_user["uid"],
        "userRole": profile.get("role", "user"),
        "alias": profile.get("alias"),
        "createdAt": created_at,
        "distress": distress,
        "moodTag": body.moodTag,
        "imageUrls": body.imageUrls or [],
        "reactionCounts": {"support": 0, "relate": 0, "care": 0},
        "commentCount": 0,
    }

    db.collection("posts").document(post_id).set(post_record)

    return PostResponse(**post_record, userReaction=None)


@router.get("", response_model=List[PostResponse])
async def list_posts(limit: int = 20, current_user=Depends(get_current_user)):
    db = get_db()
    docs = (
        db.collection("posts")
        .order_by("createdAt", direction="DESCENDING")
        .limit(limit)
        .stream()
    )

    posts: List[PostResponse] = []
    for doc in docs:
        data = doc.to_dict()

        # Check user's reaction, if any
        reaction = (
            db.collection("reactions")
            .where("postId", "==", data["id"])
            .where("userId", "==", current_user["uid"])
            .limit(1)
            .stream()
        )
        user_reaction = None
        for r in reaction:
            user_reaction = r.to_dict().get("type")
            break

        posts.append(PostResponse(**data, userReaction=user_reaction))
    return posts


@router.get("/{post_id}", response_model=PostResponse)
async def get_post(post_id: str, current_user=Depends(get_current_user)):
    db = get_db()
    snap = db.collection("posts").document(post_id).get()
    if not snap.exists:
        raise HTTPException(status_code=404, detail="Post not found")

    data = snap.to_dict()

    user_reaction = None
    reaction = (
        db.collection("reactions")
        .where("postId", "==", post_id)
        .where("userId", "==", current_user["uid"])
        .limit(1)
        .stream()
    )
    for r in reaction:
        user_reaction = r.to_dict().get("type")
        break

    return PostResponse(**data, userReaction=user_reaction)
