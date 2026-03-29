from fastapi import APIRouter, HTTPException, Depends, Header
from firebase_admin import auth as firebase_auth
from backend.firebase_config import get_db
from backend.models import ReactionRequest, ReactionResponse
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

@router.post("/{post_id}/react", response_model=ReactionResponse)
async def add_reaction(
    post_id: str,
    req: ReactionRequest,
    current_user = Depends(verify_token)
):
    """Add or update a reaction to a post"""
    db = get_db()
    
    # Validate post exists
    post_doc = db.collection("posts").document(post_id).get()
    if not post_doc.exists:
        raise HTTPException(status_code=404, detail="Post not found")
    
    # Validate reaction type
    if req.type not in ["support", "relate", "care"]:
        raise HTTPException(status_code=400, detail="Invalid reaction type")
    
    # Check if user already reacted
    existing_reaction = None
    reactions_ref = db.collection("reactions").where(
        "postId", "==", post_id
    ).where(
        "userId", "==", current_user["uid"]
    ).limit(1)
    
    for doc in reactions_ref.stream():
        existing_reaction = doc.to_dict()
        existing_reaction_id = doc.id
        break
    
    # If reacting with same type, remove the reaction
    if existing_reaction and existing_reaction.get("type") == req.type:
        # Remove reaction
        db.collection("reactions").document(existing_reaction_id).delete()
        
        # Update post reaction count
        post_data = post_doc.to_dict()
        post_data["reactionCounts"][req.type] -= 1
        db.collection("posts").document(post_id).update(post_data)
        
        raise HTTPException(status_code=200, detail="Reaction removed")
    
    # If different reaction, update it
    if existing_reaction:
        old_type = existing_reaction.get("type")
        
        db.collection("reactions").document(existing_reaction_id).update({
            "type": req.type,
            "createdAt": datetime.now().isoformat()
        })
        
        # Update post reaction counts
        post_data = post_doc.to_dict()
        post_data["reactionCounts"][old_type] -= 1
        post_data["reactionCounts"][req.type] += 1
        db.collection("posts").document(post_id).update(post_data)
        
        return ReactionResponse(
            id=existing_reaction_id,
            postId=post_id,
            userId=current_user["uid"],
            type=req.type,
            createdAt=datetime.now().isoformat()
        )
    
    # Create new reaction
    reaction_id = str(uuid.uuid4())
    reaction_data = {
        "id": reaction_id,
        "postId": post_id,
        "userId": current_user["uid"],
        "type": req.type,
        "createdAt": datetime.now().isoformat(),
    }
    
    db.collection("reactions").document(reaction_id).set(reaction_data)
    
    # Update post reaction count
    post_data = post_doc.to_dict()
    post_data["reactionCounts"][req.type] += 1
    db.collection("posts").document(post_id).update(post_data)
    
    return ReactionResponse(**reaction_data)

@router.delete("/{post_id}/react")
async def remove_reaction(
    post_id: str,
    current_user = Depends(verify_token)
):
    """Remove user's reaction from a post"""
    db = get_db()
    
    # Find and delete reaction
    reactions_ref = db.collection("reactions").where(
        "postId", "==", post_id
    ).where(
        "userId", "==", current_user["uid"]
    ).limit(1)
    
    reaction_to_delete = None
    for doc in reactions_ref.stream():
        reaction_to_delete = doc.to_dict()
        reaction_id = doc.id
        break
    
    if not reaction_to_delete:
        raise HTTPException(status_code=404, detail="Reaction not found")
    
    # Delete reaction
    db.collection("reactions").document(reaction_id).delete()
    
    # Update post reaction count
    post_doc = db.collection("posts").document(post_id).get()
    post_data = post_doc.to_dict()
    post_data["reactionCounts"][reaction_to_delete["type"]] -= 1
    db.collection("posts").document(post_id).update(post_data)
    
    return {"message": "Reaction removed"}

@router.get("/{post_id}/reactions")
async def get_reactions(
    post_id: str,
    current_user = Depends(verify_token)
):
    """Get all reactions for a post"""
    db = get_db()
    
    reactions = []
    reactions_ref = db.collection("reactions").where(
        "postId", "==", post_id
    ).stream()
    
    for doc in reactions_ref:
        reactions.append(doc.to_dict())
    
    return reactions
