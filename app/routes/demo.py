import json
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.config import get_settings
from app.db import get_session, reset_database
from scripts.seed_demo_data import seed_demo_data

router = APIRouter(prefix="/api/demo", tags=["demo"])

SAMPLE_DIR = Path(__file__).resolve().parents[2] / "sample_payloads"


@router.post("/seed")
def seed(db: Session = Depends(get_session)):
    seed_demo_data(db)
    return {"status": "seeded"}


@router.delete("/reset")
def reset():
    if not get_settings().demo_mode:
        raise HTTPException(status_code=403, detail="reset is only available in demo mode")
    reset_database()
    seed_demo_data()
    return {"status": "reset"}


@router.get("/sample-payloads")
def samples():
    return {path.name: json.loads(path.read_text(encoding="utf-8")) for path in sorted(SAMPLE_DIR.glob("*.json"))}
