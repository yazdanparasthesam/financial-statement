from fastapi import APIRouter

from .. import schemas
from ..config import get_settings

router = APIRouter(tags=["ops"])


@router.get("/healthz", response_model=schemas.HealthOut)
def healthz():
    return {"status": "ok"}


@router.get("/version", response_model=schemas.VersionOut)
def version():
    s = get_settings()
    return {"app": s.app_name, "version": s.version, "ai_provider": s.ai_provider}
