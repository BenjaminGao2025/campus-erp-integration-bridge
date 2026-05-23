def test_generated_payroll_xml_passes_xsd_validation(client):
    from app.validation.xml_validator import generate_payroll_xml, validate_payroll_xml

    xml_body = generate_payroll_xml(
        {
            "canonical_event_id": "EVT-TEST",
            "request_id": "REQ-TEST",
            "subject": {"worker_id": "WKR-10002"},
            "data": {
                "pay_period_start": "2026-06-01",
                "pay_period_end": "2026-06-15",
                "correction_type": "underpayment",
                "amount": 650.0,
                "currency": "CAD",
                "reason": "Synthetic payroll correction for missed earning code in the demo period.",
            },
        }
    )

    result = validate_payroll_xml(xml_body)
    assert result["valid"] is True


def test_malformed_payroll_xml_fails_xsd_validation(client):
    from app.validation.xml_validator import validate_payroll_xml

    result = validate_payroll_xml("<PayrollCorrection><WorkerId>bad</WorkerId></PayrollCorrection>")
    assert result["valid"] is False
