import logging
from backend.cognee.client import get_memory

logger = logging.getLogger(__name__)

async def get_user_context(user_id: str) -> str:
    try:
        return await get_memory(user_id)
    except Exception as e:
        logger.error(f"get_user_context failed for user {user_id}: {e}")
        return ""
