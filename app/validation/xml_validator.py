from pathlib import Path
from xml.sax.saxutils import escape

from lxml import etree

XSD_PATH = Path(__file__).resolve().parents[2] / "schemas" / "payroll_correction_outbound.xsd"


def generate_payroll_xml(canonical_event: dict) -> str:
    data = canonical_event["data"]
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<PayrollCorrection>
  <CanonicalEventId>{escape(str(canonical_event["canonical_event_id"]))}</CanonicalEventId>
  <RequestId>{escape(str(canonical_event["request_id"]))}</RequestId>
  <WorkerId>{escape(str(canonical_event["subject"]["worker_id"]))}</WorkerId>
  <PayPeriodStart>{escape(str(data["pay_period_start"]))}</PayPeriodStart>
  <PayPeriodEnd>{escape(str(data["pay_period_end"]))}</PayPeriodEnd>
  <CorrectionType>{escape(str(data["correction_type"]))}</CorrectionType>
  <Amount>{float(data["amount"]):.2f}</Amount>
  <Currency>{escape(str(data["currency"]))}</Currency>
  <Reason>{escape(str(data["reason"]))}</Reason>
</PayrollCorrection>"""


def validate_payroll_xml(xml_body: str) -> dict:
    try:
        schema_doc = etree.parse(str(XSD_PATH))
        schema = etree.XMLSchema(schema_doc)
        doc = etree.fromstring(xml_body.encode("utf-8"))
        schema.assertValid(doc)
        return {"valid": True, "errors": []}
    except Exception as exc:
        return {"valid": False, "errors": [str(exc)]}
