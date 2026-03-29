from fastapi import APIRouter, HTTPException, Depends, Header
from firebase_admin import auth as firebase_auth
from backend.firebase_config import get_db
from backend.models import CreatePostRequest, PostResponse
from datetime import datetime
from typing import Optional
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

@router.post("", response_model=PostResponse)
async def create_post(req: CreatePostRequest, current_user = Depends(verify_token)):
    """Create a new post"""
    if not req.content.strip():
        raise HTTPException(status_code=400, detail="Content cannot be empty")
    
    db = get_db()
    
    # Get user role from Firestore
    user_doc = db.collection("users").document(current_user["uid"]).get()
    user_data = user_doc.to_dict() if user_doc.exists else {}
    user_role = user_data.get("role", "user")
    
    # Create post
    post_id = str(uuid.uuid4())
    post_data = {
        "id": post_id,
        "content": req.content,
        "userId": current_user["uid"],
        "userRole": user_role,
        "createdAt": datetime.now().isoformat(),
        "reactionCounts": {
            "support": 0,
            "relate": 0,
            "care": 0,
        },
        "commentCount": 0,
    }
    
    db.collection("posts").document(post_id).set(post_data)
    
    return PostResponse(
        **post_data,
        userReaction=None,
    )

@router.get("", response_model=list[PostResponse])
async def get_posts(
    page: int = 1,
    limit: int = 10,
    current_user = Depends(verify_token)
):
    """Get all posts (newest first)"""
    db = get_db()
    
    # Get posts sorted by creation date (newest first)
    posts_ref = db.collection("posts").order_by(
        "createdAt", 
        direction="DESCENDING"
    ).limit(limit)
    
    posts = []
    for doc in posts_ref.stream():
        post_data = doc.to_dict()
        
        # Check if user has reacted
        user_reaction = None
        reactions_ref = db.collection("reactions").where(
            "postId", "==", post_data["id"]
        ).where(
            "userId", "==", current_user["uid"]
        ).limit(1)
        
        for reaction_doc in reactions_ref.stream():
            user_reaction = reaction_doc.to_dict().get("type")
            break
        
        posts.append(PostResponse(
            **post_data,
            userReaction=user_reaction
        ))
    
    return posts

@router.get("/{post_id}", response_model=PostResponse)
async def get_post(post_id: str, current_user = Depends(verify_token)):
    """Get a specific post"""
    db = get_db()
    doc = db.collection("posts").document(post_id).get()
    
    if not doc.exists:
        raise HTTPException(status_code=404, detail="Post not found")
    
    post_data = doc.to_dict()
    
    # Check user reaction
    user_reaction = None
    reactions_ref = db.collection("reactions").where(
        "postId", "==", post_id
    ).where(
        "userId", "==", current_user["uid"]
    ).limit(1)
    
    for reaction_doc in reactions_ref.stream():
        user_reaction = reaction_doc.to_dict().get("type")
        break
    
    return PostResponse(
        **post_data,
        userReaction=user_reaction
    )
