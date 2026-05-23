from datetime import date, datetime, timezone
from uuid import uuid4

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Integer, Numeric, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import JSON

from app.db import Base


def new_uuid() -> str:
    return str(uuid4())


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Request(Base):
    __tablename__ = "requests"
    __table_args__ = (UniqueConstraint("idempotency_key", name="uq_requests_idempotency_key"),)

    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_uuid)
    request_type: Mapped[str] = mapped_column(String, nullable=False)
    source: Mapped[str] = mapped_column(String, default="mock_service_portal", nullable=False)
    submitted_by: Mapped[str] = mapped_column(String, nullable=False)
    submitted_by_email: Mapped[str] = mapped_column(String, nullable=False)
    status: Mapped[str] = mapped_column(String, default="received", nullable=False)
    priority: Mapped[str] = mapped_column(String, default="medium", nullable=False)
    correlation_id: Mapped[str] = mapped_column(String, index=True, nullable=False)
    idempotency_key: Mapped[str | None] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)

    payloads = relationship("RequestPayload", back_populates="request", cascade="all, delete-orphan")
    approvals = relationship("ApprovalTask", back_populates="request", cascade="all, delete-orphan")
    jobs = relationship("IntegrationJob", back_populates="request", cascade="all, delete-orphan")
    artifacts = relationship("IntegrationArtifact", back_populates="request", cascade="all, delete-orphan")
    audit_events = relationship("AuditEvent", back_populates="request", cascade="all, delete-orphan")
    support_notes = relationship("SupportNote", back_populates="request", cascade="all, delete-orphan")


class RequestPayload(Base):
    __tablename__ = "request_payloads"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_uuid)
    request_id: Mapped[str] = mapped_column(ForeignKey("requests.id"), nullable=False)
    raw_payload: Mapped[dict] = mapped_column(JSON, nullable=False)
    normalized_payload: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    schema_version: Mapped[str] = mapped_column(String, default="2026-05-demo", nullable=False)
    payload_hash: Mapped[str] = mapped_column(String, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)

    request = relationship("Request", back_populates="payloads")


class ApprovalTask(Base):
    __tablename__ = "approval_tasks"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_uuid)
    request_id: Mapped[str] = mapped_column(ForeignKey("requests.id"), nullable=False)
    approver_role: Mapped[str] = mapped_column(String, nullable=False)
    status: Mapped[str] = mapped_column(String, default="pending", nullable=False)
    decision: Mapped[str | None] = mapped_column(String, nullable=True)
    decision_by: Mapped[str | None] = mapped_column(String, nullable=True)
    decision_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    comment: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)

    request = relationship("Request", back_populates="approvals")


class IntegrationJob(Base):
    __tablename__ = "integration_jobs"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_uuid)
    request_id: Mapped[str] = mapped_column(ForeignKey("requests.id"), nullable=False)
    adapter_type: Mapped[str] = mapped_column(String, nullable=False)
    target_system: Mapped[str] = mapped_column(String, nullable=False)
    status: Mapped[str] = mapped_column(String, default="pending", nullable=False)
    attempt_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    max_attempts: Mapped[int] = mapped_column(Integer, default=3, nullable=False)
    next_retry_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_error_code: Mapped[str | None] = mapped_column(String, nullable=True)
    last_error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)

    request = relationship("Request", back_populates="jobs")
    artifacts = relationship("IntegrationArtifact", back_populates="job", cascade="all, delete-orphan")


class IntegrationArtifact(Base):
    __tablename__ = "integration_artifacts"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_uuid)
    job_id: Mapped[str] = mapped_column(ForeignKey("integration_jobs.id"), nullable=False)
    request_id: Mapped[str] = mapped_column(ForeignKey("requests.id"), nullable=False)
    payload_format: Mapped[str] = mapped_column(String, nullable=False)
    payload_body: Mapped[str] = mapped_column(Text, nullable=False)
    payload_hash: Mapped[str] = mapped_column(String, nullable=False)
    validation_result: Mapped[dict] = mapped_column(JSON, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)

    job = relationship("IntegrationJob", back_populates="artifacts")
    request = relationship("Request", back_populates="artifacts")


class AuditEvent(Base):
    __tablename__ = "audit_events"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_uuid)
    request_id: Mapped[str | None] = mapped_column(ForeignKey("requests.id"), nullable=True)
    correlation_id: Mapped[str] = mapped_column(String, nullable=False, index=True)
    actor_type: Mapped[str] = mapped_column(String, nullable=False)
    actor_id: Mapped[str | None] = mapped_column(String, nullable=True)
    event_type: Mapped[str] = mapped_column(String, nullable=False)
    before_state: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    after_state: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    payload_hash: Mapped[str | None] = mapped_column(String, nullable=True)
    validation_result: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    error_code: Mapped[str | None] = mapped_column(String, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    redaction_flags: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    meta: Mapped[dict] = mapped_column("metadata", JSON, default=dict, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)

    request = relationship("Request", back_populates="audit_events")


class MockWorker(Base):
    __tablename__ = "mock_workers"

    worker_id: Mapped[str] = mapped_column(String, primary_key=True)
    full_name: Mapped[str] = mapped_column(String, nullable=False)
    department: Mapped[str] = mapped_column(String, nullable=False)
    manager_id: Mapped[str] = mapped_column(String, nullable=False)
    employment_status: Mapped[str] = mapped_column(String, nullable=False)
    location: Mapped[str] = mapped_column(String, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)


class MockPayrollRecord(Base):
    __tablename__ = "mock_payroll_records"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_uuid)
    worker_id: Mapped[str] = mapped_column(String, nullable=False)
    pay_period_start: Mapped[date] = mapped_column(Date, nullable=False)
    pay_period_end: Mapped[date] = mapped_column(Date, nullable=False)
    issue_type: Mapped[str] = mapped_column(String, nullable=False)
    amount: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String, default="CAD", nullable=False)
    status: Mapped[str] = mapped_column(String, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)


class SupportNote(Base):
    __tablename__ = "support_notes"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_uuid)
    request_id: Mapped[str] = mapped_column(ForeignKey("requests.id"), nullable=False)
    note_type: Mapped[str] = mapped_column(String, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    created_by: Mapped[str] = mapped_column(String, nullable=False)
    is_ai_generated: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)

    request = relationship("Request", back_populates="support_notes")


class PolicyDoc(Base):
    __tablename__ = "policy_docs"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_uuid)
    domain: Mapped[str] = mapped_column(String, nullable=False)
    title: Mapped[str] = mapped_column(String, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
