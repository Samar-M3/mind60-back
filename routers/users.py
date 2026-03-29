from typing import List
from fastapi import APIRouter, Depends, HTTPException

from backend.core.security import get_current_user, assert_admin_user
from backend.models import PendingRoleRequest, RoleApprovalAction, RoleApprovalResponse
from backend.services.firestore_service import (
    approve_role_request,
    get_mood_history,
    list_pending_role_requests,
    reject_role_request,
    save_mood_entry,
)

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me/mood")
async def get_my_mood(current_user=Depends(get_current_user)):
    return {"entries": get_mood_history(current_user["uid"])}


@router.post("/me/mood")
async def log_my_mood(value: int, current_user=Depends(get_current_user)):
    if value < 1 or value > 5:
        raise HTTPException(status_code=400, detail="Mood must be between 1 and 5")
    entry = save_mood_entry(current_user["uid"], value)
    return {"entry": entry}


@router.get("/admin/role-requests", response_model=List[PendingRoleRequest])
async def get_pending_role_requests(current_user=Depends(get_current_user)):
    assert_admin_user(current_user)
    return [PendingRoleRequest(**item) for item in list_pending_role_requests()]


@router.post(
    "/admin/role-requests/{uid}/approve",
    response_model=RoleApprovalResponse,
)
async def approve_requested_role(
    uid: str,
    body: RoleApprovalAction,
    current_user=Depends(get_current_user),
):
    assert_admin_user(current_user)
    try:
        result = approve_role_request(uid, body.approvedRole)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    return RoleApprovalResponse(**result)


@router.post(
    "/admin/role-requests/{uid}/reject",
    response_model=RoleApprovalResponse,
)
async def reject_requested_role(uid: str, current_user=Depends(get_current_user)):
    assert_admin_user(current_user)
    try:
        result = reject_role_request(uid)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    return RoleApprovalResponse(**result)

