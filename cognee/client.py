import os
import httpx
import logging
import asyncio

logger = logging.getLogger(__name__)

COGNEE_API_URL = os.getenv("COGNEE_API_URL", "https://api.cognee.ai/v1")
COGNEE_API_KEY = os.getenv("COGNEE_API_KEY", "")

async def add_memory(user_id: str, summary: str):
    if not COGNEE_API_KEY:
        return
    try:
        async with httpx.AsyncClient(timeout=3.0) as client:
            headers = {"Authorization": f"Bearer {COGNEE_API_KEY}"}
            await client.post(
                f"{COGNEE_API_URL}/memory",
                json={"user_id": user_id, "text": summary},
                headers=headers
            )
    except Exception as e:
        logger.error(f"Cognee add_memory failed for user {user_id}: {e}")

async def get_memory(user_id: str) -> str:
    if not COGNEE_API_KEY:
        return ""
    try:
        async with httpx.AsyncClient(timeout=3.0) as client:
            headers = {"Authorization": f"Bearer {COGNEE_API_KEY}"}
            resp = await client.get(f"{COGNEE_API_URL}/memory/{user_id}", headers=headers)
            resp.raise_for_status()
            data = resp.json()
            # Try to extract a summary text, fallback to str(data)
            return data.get("summary", data.get("text", ""))
    except Exception as e:
        logger.error(f"Cognee get_memory failed for user {user_id}: {e}")
        return ""

async def delete_memory(user_id: str) -> bool:
    if not COGNEE_API_KEY:
        return False
    try:
        async with httpx.AsyncClient(timeout=3.0) as client:
            headers = {"Authorization": f"Bearer {COGNEE_API_KEY}"}
            resp = await client.delete(f"{COGNEE_API_URL}/memory/{user_id}", headers=headers)
            resp.raise_for_status()
            return True
    except Exception as e:
        logger.error(f"Cognee delete_memory failed for user {user_id}: {e}")
        return False
