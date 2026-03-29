from pydantic import BaseModel, Field


class CommentCreate(BaseModel):
    content: str = Field(min_length=1, max_length=1000)


class CommentResponse(BaseModel):
    id: str
    postId: str
    content: str
    authorId: str
    authorRole: str
    createdAt: str

