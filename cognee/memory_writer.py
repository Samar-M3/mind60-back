import asyncio
import logging
import os
from typing import Optional
from backend.cognee.client import add_memory
from backend.services.chatbot_service import anthropic

logger = logging.getLogger(__name__)

def summarize_and_store(user_id: str, chat_turn: str, mood_checkin: Optional[dict] = None) -> None:
    # Call this fire-and-forget after each chat turn and after each mood check-in
    asyncio.create_task(_run_summarize_and_store(user_id, chat_turn, mood_checkin))

async def _run_summarize_and_store(user_id: str, chat_turn: str, mood_checkin: Optional[dict]):
    try:
        api_key = os.getenv("ANTHROPIC_API_KEY")
        summary = chat_turn
        if api_key and anthropic is not None:
            client = anthropic.Anthropic(api_key=api_key)
            prompt = f"Summarize this mental health chat turn neutrally (theme + mood + what helped, if anything) for long term memory without recording raw verbatim messages: {chat_turn}"
            if mood_checkin:
                prompt += f" Recent mood checkin data: {mood_checkin}"
            
            completion = client.messages.create(
                model="claude-3-haiku-20240307",
                max_tokens=150,
                system="You are an AI assistant creating short neutral summaries. Never use clinical diagnoses.",
                messages=[{"role": "user", "content": prompt}],
            )
            if completion and completion.content:
                text_parts = [c.text for c in completion.content if hasattr(c, "text")]
                if text_parts:
                    summary = text_parts[0]
        
        await add_memory(user_id, summary)
    except Exception as e:
        logger.error(f"summarize_and_store failed for user {user_id}: {e}")
