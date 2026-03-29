from fastapi import APIRouter, HTTPException, Depends, Header
from firebase_admin import auth as firebase_auth
from backend.firebase_config import get_db
from backend.models import CreateCommentRequest, CommentResponse
from datetime import datetime
import uuid

router = APIRouter()

async def verify_token(authorization: str = Header(None)):
    """Verify Firebase token from Authorization header"""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing authorization token")
    
    token = authorization.split(" ")[1]
    try:
        decoded_token = firebase_auth.verify_id_token(token)
        return decoded_token
    except Exception as e:
        raise HTTPException(status_code=401, detail="Invalid token")

@router.post("/{post_id}/comment", response_model=CommentResponse)
async def add_comment(
    post_id: str,
    req: CreateCommentRequest,
    current_user = Depends(verify_token)
):
    """Add a comment to a post (only professionals can comment)"""
    db = get_db()
    
    # Validate post exists
    post_doc = db.collection("posts").document(post_id).get()
    if not post_doc.exists:
        raise HTTPException(status_code=404, detail="Post not found")
    
    # Get user role and verify permission
    user_doc = db.collection("users").document(current_user["uid"]).get()
    if not user_doc.exists:
        raise HTTPException(status_code=404, detail="User not found")
    
    user_data = user_doc.to_dict()
    user_role = user_data.get("role", "user")
    
    # Only professionals can comment
    if user_role not in ["doctor", "therapist", "psychiatrist"]:
        raise HTTPException(
            status_code=403,
            detail="Only professionals (doctor, therapist, psychiatrist) can comment"
        )
    
    if not req.content.strip():
        raise HTTPException(status_code=400, detail="Comment cannot be empty")
    
    # Create comment
    comment_id = str(uuid.uuid4())
    comment_data = {
        "id": comment_id,
        "postId": post_id,
        "content": req.content,
        "authorId": current_user["uid"],
        "authorRole": user_role,
        "createdAt": datetime.now().isoformat(),
    }
    
    db.collection("comments").document(comment_id).set(comment_data)
    
    # Update post comment count
    post_data = post_doc.to_dict()
    post_data["commentCount"] = post_data.get("commentCount", 0) + 1
    db.collection("posts").document(post_id).update({"commentCount": post_data["commentCount"]})
    
    return CommentResponse(**comment_data)

@router.get("/{post_id}/comments", response_model=list[CommentResponse])
async def get_comments(
    post_id: str,
    current_user = Depends(verify_token)
):
    """Get all comments for a post"""
    db = get_db()
    
    # Validate post exists
    post_doc = db.collection("posts").document(post_id).get()
    if not post_doc.exists:
        raise HTTPException(status_code=404, detail="Post not found")
    
    comments = []
    comments_ref = db.collection("comments").where(
        "postId", "==", post_id
    ).order_by("createdAt").stream()
    
    for doc in comments_ref:
        comments.append(CommentResponse(**doc.to_dict()))
    
    return comments

@router.delete("/{post_id}/comments/{comment_id}")
async def delete_comment(
    post_id: str,
    comment_id: str,
    current_user = Depends(verify_token)
):
    """Delete a comment (author only)"""
    db = get_db()
    
    # Get comment
    comment_doc = db.collection("comments").document(comment_id).get()
    if not comment_doc.exists:
        raise HTTPException(status_code=404, detail="Comment not found")
    
    comment_data = comment_doc.to_dict()
    
    # Verify ownership
    if comment_data["authorId"] != current_user["uid"]:
        raise HTTPException(status_code=403, detail="Can only delete your own comments")
    
    # Delete comment
    db.collection("comments").document(comment_id).delete()
    
    # Update post comment count
    post_doc = db.collection("posts").document(post_id).get()
    if post_doc.exists:
        post_data = post_doc.to_dict()
        post_data["commentCount"] = max(0, post_data.get("commentCount", 1) - 1)
        db.collection("posts").document(post_id).update({"commentCount": post_data["commentCount"]})
    
    return {"message": "Comment deleted"}
