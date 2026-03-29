from datetime import datetime, timezone
import uuid
from typing import List

from fastapi import APIRouter, Depends, HTTPException

from backend.core.security import get_current_user, assert_professional_role
from backend.models import CommentCreate, CommentResponse
from backend.core.firebase import get_db

router = APIRouter(prefix="/posts", tags=["comments"])


@router.post("/{post_id}/comment", response_model=CommentResponse)
async def add_comment(
    post_id: str, body: CommentCreate, current_user=Depends(get_current_user)
):
    db = get_db()
    post_doc = db.collection("posts").document(post_id).get()
    if not post_doc.exists:
        raise HTTPException(status_code=404, detail="Post not found")

    # Only professionals can comment
    user_doc = db.collection("users").document(current_user["uid"]).get()
    if not user_doc.exists:
        raise HTTPException(status_code=404, detail="User not found")

    user_role = user_doc.to_dict().get("role", "user")
    assert_professional_role(user_role)

    comment_id = str(uuid.uuid4())
    created_at = datetime.now(timezone.utc).isoformat()
    comment_record = {
        "id": comment_id,
        "postId": post_id,
        "content": body.content,
        "authorId": current_user["uid"],
        "authorRole": user_role,
        "createdAt": created_at,
    }
    db.collection("comments").document(comment_id).set(comment_record)

    # Increment commentCount
    post_data = post_doc.to_dict()
    post_data["commentCount"] = post_data.get("commentCount", 0) + 1
    db.collection("posts").document(post_id).update(
        {"commentCount": post_data["commentCount"]}
    )

    return CommentResponse(**comment_record)


@router.get("/{post_id}/comments", response_model=List[CommentResponse])
async def list_comments(post_id: str, current_user=Depends(get_current_user)):
    db = get_db()
    post_doc = db.collection("posts").document(post_id).get()
    if not post_doc.exists:
        raise HTTPException(status_code=404, detail="Post not found")

    comments = []
    for doc in (
        db.collection("comments")
        .where("postId", "==", post_id)
        .order_by("createdAt")
        .stream()
    ):
        comments.append(CommentResponse(**doc.to_dict()))

    return comments


@router.delete("/{post_id}/comments/{comment_id}")
async def delete_comment(
    post_id: str, comment_id: str, current_user=Depends(get_current_user)
):
    db = get_db()
    doc = db.collection("comments").document(comment_id).get()
    if not doc.exists:
        raise HTTPException(status_code=404, detail="Comment not found")

    data = doc.to_dict()
    if data.get("authorId") != current_user["uid"]:
        raise HTTPException(status_code=403, detail="Can only delete your own comments")

    db.collection("comments").document(comment_id).delete()
    post_doc = db.collection("posts").document(post_id).get()
    if post_doc.exists:
        counts = max(0, post_doc.to_dict().get("commentCount", 1) - 1)
        db.collection("posts").document(post_id).update({"commentCount": counts})

    return {"message": "Comment deleted"}

