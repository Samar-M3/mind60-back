from fastapi import APIRouter, Depends, HTTPException
from backend.core.security import get_current_user
from backend.cognee.client import get_memory, delete_memory

router = APIRouter(prefix="/user/memory", tags=["memory"])

@router.get("")
async def get_my_memory(current_user=Depends(get_current_user)):
    user_id = current_user["uid"]
    try:
        summary = await get_memory(user_id)
        return {"summary": summary}
    except Exception as e:
        return {"summary": ""}

@router.delete("")
async def clear_my_memory(current_user=Depends(get_current_user)):
    user_id = current_user["uid"]
    try:
        success = await delete_memory(user_id)
        if success:
            return {"status": "success", "message": "Memory cleared."}
        else:
            return {"status": "error", "message": "Failed to clear memory or not configured."}
    except Exception as e:
        return {"status": "error", "message": str(e)}
