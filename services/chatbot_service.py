"""
Chatbot service ("Sathi") with optional Anthropic integration and safe mocks.
"""

import os
from typing import List, Optional

try:
    import anthropic  # type: ignore
except Exception:
    anthropic = None

SYSTEM_PROMPT = """
You are Sathi 🌿, a compassionate, CBT-informed mental health companion.
- You listen with warmth, validate feelings, and keep responses concise.
- You are NOT a replacement for professional care; suggest professional help for serious issues.
- If you detect crisis language (suicide, hurt myself, end it all), gently surface crisis resources and Lifeline Nepal (16000).
- Offer grounding: 4-7-8 breath, 5-4-3-2-1 senses, or gentle reframes.
"""

MOCK_RESPONSES = [
    "I hear you. That sounds really hard. Can you tell me more about what's been going on?",
    "It makes sense that you'd feel that way. Your feelings are completely valid 💙",
    "Have you tried taking a few slow deep breaths? Sometimes that can help ground us.",
    "You're not alone in this. Many people feel exactly what you're describing.",
    "Would it help to talk to one of our verified professionals on MindSathi?",
]

CRISIS_KEYWORDS = ["suicide", "kill myself", "end it", "end it all", "hurt myself", "hopeless"]


def _crisis_response() -> str:
    return (
        "I’m really sorry you’re feeling this way. You matter. "
        "If you can, please reach out to someone you trust or call a crisis line now. "
        "In Nepal, Lifeline (Suicide Prevention Hotline) is available at 16000 or +977-1-426-3450. "
        "Would you like me to show crisis resources?"
    )


async def get_chatbot_response(message: str, history: Optional[List[dict]] = None) -> str:
    msg = message.lower()
    if any(word in msg for word in CRISIS_KEYWORDS):
        return _crisis_response()

    # Anthropic if available and key set
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if api_key and anthropic is not None:
        try:
            client = anthropic.Anthropic(api_key=api_key)
            conv = []
            if history:
                for turn in history[-6:]:
                    conv.append({"role": turn.get("role", "user"), "content": turn.get("content", "")})
            conv.append({"role": "user", "content": message})
            completion = client.messages.create(
                model="claude-3-sonnet-20240229",
                max_tokens=250,
                system=SYSTEM_PROMPT,
                messages=conv,
            )
            # Anthropic SDK returns content list; take text part
            if completion and completion.content:
                text_parts = [c.text for c in completion.content if hasattr(c, "text")]
                if text_parts:
                    return text_parts[0]
        except Exception:
            # fall back to mock below
            pass

    # Mock fallback
    from random import choice
    return choice(MOCK_RESPONSES)
