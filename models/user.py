from typing import Literal, Optional
from pydantic import BaseModel


class UserProfile(BaseModel):
    uid: str
    email: Optional[str] = None
    displayName: Optional[str] = None
    role: str = "user"
    requestedRole: Optional[str] = None
    alias: str
    createdAt: str


class PendingRoleRequest(BaseModel):
    uid: str
    email: Optional[str] = None
    alias: str
    role: str = "user"
    requestedRole: Literal["doctor", "therapist", "psychiatrist"]
    createdAt: str


class RoleApprovalAction(BaseModel):
    approvedRole: Literal["doctor", "therapist", "psychiatrist"]


class RoleApprovalResponse(BaseModel):
    uid: str
    role: str
    requestedRole: Optional[str] = None
    updatedAt: str

