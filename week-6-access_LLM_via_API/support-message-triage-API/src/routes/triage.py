from fastapi import APIRouter

from src.llm.schema import TriageRes, TriageReq

router = APIRouter()

@router.post('/triage',response_model=TriageRes)
def triage(req:TriageReq):
    return TriageRes(
        catagory="other",
        urgency="normal",
        confidence=0.1,
        reason="stub response for development"
    )