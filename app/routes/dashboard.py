from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db import get_session
from app.services.metrics_service import dashboard_metrics

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


@router.get("/metrics")
def metrics(db: Session = Depends(get_session)):
    return dashboard_metrics(db)
