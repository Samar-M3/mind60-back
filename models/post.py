from typing import Dict, Literal, Optional
from pydantic import BaseModel, Field, field_validator


MoodTag = Literal["sad", "anxious", "frustrated", "numb", "hopeful"]


class DistressResult(BaseModel):
    score: int = Field(ge=0, le=100)
    level: Literal["low", "medium", "high", "critical"]


class PostCreate(BaseModel):
    content: str = Field(min_length=1, max_length=1000)
    moodTag: Optional[MoodTag] = None
    imageUrls: list[str] = Field(default_factory=list, max_length=4)

    @field_validator("content")
    @classmethod
    def validate_content(cls, value: str) -> str:
        trimmed = value.strip()
        if not trimmed:
            raise ValueError("Content cannot be empty")
        return trimmed

    @field_validator("imageUrls")
    @classmethod
    def validate_image_urls(cls, value: list[str]) -> list[str]:
        allowed_prefixes = (
            "https://firebasestorage.googleapis.com/",
            "https://storage.googleapis.com/",
        )
        for item in value:
            if not item.startswith(allowed_prefixes):
                raise ValueError("Image URLs must come from approved storage")
        return value


class PostResponse(BaseModel):
    id: str
    content: str
    userId: str
    userRole: str
    alias: str
    createdAt: str
    reactionCounts: Dict[str, int]
    userReaction: Optional[str] = None
    commentCount: int
    distress: Optional[DistressResult] = None
    moodTag: Optional[MoodTag] = None
    imageUrls: list[str] = []
