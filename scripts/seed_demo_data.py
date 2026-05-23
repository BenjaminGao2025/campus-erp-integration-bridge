from sqlalchemy import select
from sqlalchemy.orm import Session

import app.db as db_module
from app.models import MockWorker, PolicyDoc


def seed_demo_data(db: Session | None = None) -> None:
    own_session = db is None
    if db is None:
        if db_module.SessionLocal is None:
            db_module.configure_database()
        assert db_module.SessionLocal is not None
        db = db_module.SessionLocal()
    workers = [
        MockWorker(worker_id="WKR-10001", full_name="Jordan Lee", department="Operations", manager_id="MGR-20001", employment_status="active", location="North Campus"),
        MockWorker(worker_id="WKR-10002", full_name="Priya Shah", department="Finance", manager_id="MGR-20002", employment_status="active", location="West Campus"),
        MockWorker(worker_id="WKR-10003", full_name="Mateo Chen", department="Student Services", manager_id="MGR-20003", employment_status="active", location="East Campus"),
    ]
    for worker in workers:
        if db.get(MockWorker, worker.worker_id) is None:
            db.add(worker)
    docs = [
        ("hcm", "Worker change approval", "Worker change requests require manager approval before integration."),
        ("payroll", "Payroll correction approval", "Payroll corrections require payroll reviewer approval before downstream processing."),
        ("ai", "AI boundary", "AI-generated summaries are advisory and must not replace deterministic validation or human approval."),
        ("support", "Retry policy", "Retry is allowed only for transient adapter failures."),
    ]
    for domain, title, content in docs:
        exists = db.execute(select(PolicyDoc).where(PolicyDoc.domain == domain, PolicyDoc.title == title)).scalar_one_or_none()
        if exists is None:
            db.add(PolicyDoc(domain=domain, title=title, content=content))
    db.commit()
    if own_session:
        db.close()


if __name__ == "__main__":
    seed_demo_data()
    print("Seeded synthetic demo data.")
