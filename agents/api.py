"""HTTP interface for NEXUS assessment and gated legacy simulation utilities."""
import os
import secrets
from typing import Optional

from fastapi import Depends, FastAPI, Header, HTTPException
from pydantic import BaseModel, Field

from nexus_cspine import calculate_metrics
from .base import AuditLogger
from .models import SystemTaskPayload
from .supervisor import SystemSupervisor

app = FastAPI(
    title="NEXUS Cervical Spine Criteria API",
    description="Five-item NEXUS decision support for blunt trauma; not a diagnosis.",
    version="3.1.0",
)
legacy_supervisor = SystemSupervisor(model_provider="mock")


class NexusAssessment(BaseModel):
    midline_tenderness: Optional[bool] = None
    intoxication: Optional[bool] = None
    altered_alertness: Optional[bool] = None
    focal_neurologic_deficit: Optional[bool] = None
    distracting_injury: Optional[bool] = None
    age: Optional[int] = Field(default=None, ge=0, le=120)


class ChatRequest(BaseModel):
    query: str


def require_legacy_access(x_api_key: Optional[str] = Header(default=None)) -> None:
    """Legacy generic components are not clinical and are off by default."""
    configured = os.environ.get("LEGACY_API_TOKEN", "")
    if os.environ.get("ENABLE_LEGACY_API") != "1" or not configured:
        raise HTTPException(status_code=404, detail="Legacy simulation API is disabled")
    if not x_api_key or not secrets.compare_digest(configured, x_api_key):
        raise HTTPException(status_code=401, detail="Invalid API key")


@app.get("/health")
def health():
    return {"status": "ok", "service": "nexus-c-spine-criteria", "version": "3.1.0"}


@app.post("/api/nexus")
def evaluate(payload: NexusAssessment):
    """Positive = unable to clear using NEXUS; negative is low-risk only."""
    return calculate_metrics(**payload.model_dump())


@app.get("/metrics", dependencies=[Depends(require_legacy_access)], deprecated=True)
def metrics():
    return {
        "legacy_dossiers_total": len(legacy_supervisor.dossier_registry),
        "legacy_audit_blocks_total": len(AuditLogger.get_trail()),
    }


@app.post("/api/audit", dependencies=[Depends(require_legacy_access)], deprecated=True)
def legacy_audit(payload: SystemTaskPayload):
    return legacy_supervisor.process_task(payload).to_dict()


@app.post("/api/chat", dependencies=[Depends(require_legacy_access)], deprecated=True)
def legacy_chat(payload: ChatRequest):
    return {"response": legacy_supervisor.query_supervisory_chat(payload.query)}


@app.get("/api/audit/logs", dependencies=[Depends(require_legacy_access)], deprecated=True)
def legacy_logs():
    return {"audit_trail": AuditLogger.get_trail(), "verified": AuditLogger.verify_integrity()}
