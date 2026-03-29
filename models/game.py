from typing import List

from pydantic import BaseModel, Field


class GameScoreSubmit(BaseModel):
    score: int = Field(ge=0, le=10000)


class GameLeaderboardEntry(BaseModel):
    uid: str
    alias: str
    score: int
    gameId: str
    updatedAt: str
    isCurrentUser: bool = False


class GameScoreResponse(BaseModel):
    gameId: str
    score: int
    bestScore: int
    isPersonalBest: bool
    updatedAt: str


class GameLeaderboardResponse(BaseModel):
    gameId: str
    entries: List[GameLeaderboardEntry]
