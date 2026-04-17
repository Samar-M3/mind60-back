from fastapi import APIRouter, Depends

from backend.core.security import get_current_user
from backend.models.wellness import WellnessAnalyzeRequest, WellnessAnalyzeResponse
from backend.services.wellness_ai_service import analyze_wellness

router = APIRouter(prefix="/wellness", tags=["wellness"])


@router.post("/analyze", response_model=WellnessAnalyzeResponse)
async def wellness_analyze(body: WellnessAnalyzeRequest, _user=Depends(get_current_user)):
    """
    Turn aggregated daily signals into burnout/stress insight + suggestions.
    """
    return await analyze_wellness(body)
