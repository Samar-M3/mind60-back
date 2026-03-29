from pydantic import BaseModel, Field


class ReactionCreate(BaseModel):
    type: str = Field(pattern="^(support|relate|care)$")


class ReactionResponse(BaseModel):
    id: str
    postId: str
    userId: str
    type: str
    createdAt: str

