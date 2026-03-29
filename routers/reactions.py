from datetime import datetime, timezone
import uuid

from fastapi import APIRouter, Depends, HTTPException

from backend.core.security import get_current_user
from backend.models import ReactionCreate, ReactionResponse
from backend.core.firebase import get_db

router = APIRouter(prefix="/posts", tags=["reactions"])


@router.post("/{post_id}/react", response_model=ReactionResponse)
async def add_reaction(
    post_id: str, body: ReactionCreate, current_user=Depends(get_current_user)
):
    db = get_db()

    post_doc = db.collection("posts").document(post_id).get()
    if not post_doc.exists:
        raise HTTPException(status_code=404, detail="Post not found")

    if body.type not in {"support", "relate", "care"}:
        raise HTTPException(status_code=400, detail="Invalid reaction type")

    # Check for existing reaction
    existing = (
        db.collection("reactions")
        .where("postId", "==", post_id)
        .where("userId", "==", current_user["uid"])
        .limit(1)
        .stream()
    )

    existing_reaction = None
    existing_id = None
    for doc in existing:
        existing_reaction = doc.to_dict()
        existing_id = doc.id
        break

    post_counts = post_doc.to_dict().get("reactionCounts", {})

    if existing_reaction and existing_reaction.get("type") == body.type:
        # remove reaction
        db.collection("reactions").document(existing_id).delete()
        post_counts[body.type] = max(0, post_counts.get(body.type, 1) - 1)
        db.collection("posts").document(post_id).update({"reactionCounts": post_counts})
        return ReactionResponse(
            id=existing_id,
            postId=post_id,
            userId=current_user["uid"],
            type=body.type,
            createdAt=existing_reaction.get("createdAt", ""),
        )

    if existing_reaction:
        old_type = existing_reaction["type"]
        post_counts[old_type] = max(0, post_counts.get(old_type, 1) - 1)

        db.collection("reactions").document(existing_id).update(
            {"type": body.type, "createdAt": datetime.now(timezone.utc).isoformat()}
        )
        post_counts[body.type] = post_counts.get(body.type, 0) + 1
        db.collection("posts").document(post_id).update({"reactionCounts": post_counts})
        return ReactionResponse(
            id=existing_id,
            postId=post_id,
            userId=current_user["uid"],
            type=body.type,
            createdAt=datetime.now(timezone.utc).isoformat(),
        )

    reaction_id = str(uuid.uuid4())
    reaction_data = {
        "id": reaction_id,
        "postId": post_id,
        "userId": current_user["uid"],
        "type": body.type,
        "createdAt": datetime.now(timezone.utc).isoformat(),
    }
    db.collection("reactions").document(reaction_id).set(reaction_data)
    post_counts[body.type] = post_counts.get(body.type, 0) + 1
    db.collection("posts").document(post_id).update({"reactionCounts": post_counts})

    return ReactionResponse(**reaction_data)


@router.delete("/{post_id}/react")
async def remove_reaction(post_id: str, current_user=Depends(get_current_user)):
    db = get_db()
    existing = (
        db.collection("reactions")
        .where("postId", "==", post_id)
        .where("userId", "==", current_user["uid"])
        .limit(1)
        .stream()
    )

    reaction_to_delete = None
    reaction_id = None
    for doc in existing:
        reaction_to_delete = doc.to_dict()
        reaction_id = doc.id
        break

    if not reaction_to_delete:
        raise HTTPException(status_code=404, detail="Reaction not found")

    db.collection("reactions").document(reaction_id).delete()

    post_doc = db.collection("posts").document(post_id).get()
    if post_doc.exists:
        counts = post_doc.to_dict().get("reactionCounts", {})
        reaction_type = reaction_to_delete.get("type")
        counts[reaction_type] = max(0, counts.get(reaction_type, 1) - 1)
        db.collection("posts").document(post_id).update({"reactionCounts": counts})

    return {"message": "Reaction removed"}

