"""
Lightweight profanity/negative-word masker.

Use a small in-memory list so the API can run without extra dependencies.
If a word is matched (case-insensitive, word-boundary), it is replaced with
the mask token (default ******). Keep this minimal to avoid over-blocking.
"""

from __future__ import annotations

import re
from typing import Iterable, Set

# Basic shortlist; extend as needed or move to env/DB if requirements grow.
DEFAULT_BANNED_WORDS: Set[str] = {
    "fuck",
    "shit",
    "bitch",
    "bastard",
    "asshole",
    "crap",
    "stupid",
    "idiot",
    "suicide",
    "kill",
}


def build_pattern(words: Iterable[str]) -> re.Pattern:
    safe_words = [re.escape(w) for w in words if w]
    if not safe_words:
        # Match nothing if list is empty
        return re.compile(r"$a", flags=re.IGNORECASE)
    return re.compile(rf"\\b({'|'.join(safe_words)})\\b", flags=re.IGNORECASE)


_DEFAULT_PATTERN = build_pattern(DEFAULT_BANNED_WORDS)


def mask_profanity(text: str, mask: str = "******", custom_words: Iterable[str] | None = None) -> str:
    """
    Replace banned words in `text` with the mask token. Returns the masked text.
    """
    pattern = _DEFAULT_PATTERN if custom_words is None else build_pattern(custom_words)
    return pattern.sub(mask, text)

