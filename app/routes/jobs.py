from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_session
from app.models import IntegrationJob
from app.routes.serializers import job_to_dict, request_to_dict
from app.services.retry_service import retry_job

router = APIRouter(prefix="/api/jobs", tags=["jobs"])


@router.get("")
def list_jobs(db: Session = Depends(get_session)):
    return [job_to_dict(item) for item in db.execute(select(IntegrationJob).order_by(IntegrationJob.created_at.desc())).scalars()]


@router.get("/{job_id}")
def get_job(job_id: str, db: Session = Depends(get_session)):
    return job_to_dict(db.get(IntegrationJob, job_id))


@router.post("/{job_id}/retry")
def retry(job_id: str, db: Session = Depends(get_session)):
    request = retry_job(db, job_id)
    return {"request_status": request.status, "request": request_to_dict(request, detail=True)}
