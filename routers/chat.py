from fastapi import APIRouter, Depends

from backend.core.security import get_current_user
from backend.models import ChatRequest, ChatResponse
from backend.services.chatbot_service import get_chatbot_response
from backend.cognee.memory_writer import summarize_and_store

router = APIRouter(prefix="/chat", tags=["chat"])

@router.post("", response_model=ChatResponse)
async def chat(body: ChatRequest, current_user=Depends(get_current_user)):
    """
    Chat with Sathi. Uses Anthropic if ANTHROPIC_API_KEY is set, otherwise a safe mock.
    Crisis phrases trigger a crisis-safe response.
    """
    user_id = current_user["uid"]
    
    reply = await get_chatbot_response(
        body.message,
        history=body.history,
        wellness_context=body.wellness_context,
        user_id=user_id,
    )
    
    summarize_and_store(user_id, body.message)
    
    return ChatResponse(reply=reply)
