REQUEST_WORKER_CHANGE = "worker_change"
REQUEST_PAYROLL_CORRECTION = "payroll_correction"

REQUEST_STATUSES = {
    "draft",
    "received",
    "validation_failed",
    "pending_approval",
    "approved",
    "rejected",
    "ready_for_integration",
    "processing",
    "completed",
    "failed_retryable",
    "failed_permanent",
    "retry_scheduled",
}

JOB_STATUSES = {
    "pending",
    "processing",
    "completed",
    "failed_retryable",
    "failed_permanent",
    "retry_scheduled",
}

EVENT_REQUEST_RECEIVED = "request_received"
EVENT_AI_SUMMARY_GENERATED = "ai_summary_generated"
EVENT_SCHEMA_VALIDATION_PASSED = "schema_validation_passed"
EVENT_SCHEMA_VALIDATION_FAILED = "schema_validation_failed"
EVENT_BUSINESS_RULES_EVALUATED = "business_rules_evaluated"
EVENT_APPROVAL_REQUESTED = "approval_requested"
EVENT_APPROVAL_APPROVED = "approval_approved"
EVENT_APPROVAL_REJECTED = "approval_rejected"
EVENT_CANONICAL_MAPPING_CREATED = "canonical_mapping_created"
EVENT_INTEGRATION_JOB_CREATED = "integration_job_created"
EVENT_ADAPTER_EXECUTION_STARTED = "adapter_execution_started"
EVENT_ADAPTER_EXECUTION_COMPLETED = "adapter_execution_completed"
EVENT_ADAPTER_EXECUTION_FAILED = "adapter_execution_failed"
EVENT_RETRY_SCHEDULED = "retry_scheduled"
EVENT_RETRY_STARTED = "retry_started"
EVENT_XML_GENERATED = "xml_generated"
EVENT_XSD_VALIDATION_PASSED = "xsd_validation_passed"
EVENT_XSD_VALIDATION_FAILED = "xsd_validation_failed"
EVENT_REQUEST_COMPLETED = "request_completed"
EVENT_REQUEST_FAILED = "request_failed"
