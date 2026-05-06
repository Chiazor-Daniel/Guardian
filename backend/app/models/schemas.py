from pydantic import BaseModel
from typing import List, Optional, Literal
from enum import Enum


class RiskLevel(str, Enum):
    SAFE = "SAFE"
    LOW_RISK = "LOW_RISK"
    MEDIUM_RISK = "MEDIUM_RISK"
    HIGH_RISK = "HIGH_RISK"
    CRITICAL_RISK = "CRITICAL_RISK"


class EvidenceItem(BaseModel):
    type: str
    detail: str
    severity: Literal["info", "warning", "critical"] = "info"


class AssetData(BaseModel):
    urls: List[dict] = []
    documents: List[dict] = []
    screenshots: List[str] = []


class AnalysisRequest(BaseModel):
    urls: List[str] = []
    user_prompt: Optional[str] = None


class AnalysisResponse(BaseModel):
    verdict: RiskLevel
    score: int
    summary: str
    evidence: List[EvidenceItem]
    recommended_action: str
    processing_time_ms: Optional[int] = None
