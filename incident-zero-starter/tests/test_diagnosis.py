import json
from pathlib import Path

from telemetry import collect_telemetry
from diagnosis import diagnose
from remediation import execute_if_approved

ROOT = Path(__file__).resolve().parents[1]

def test_sample_incident_produces_evidence_backed_hypothesis():
    incident = json.loads((ROOT / "data/incidents/checkout-timeout.json").read_text(encoding="utf-8"))
    result = diagnose(incident, collect_telemetry(incident))
    assert "payment" in result["hypothesis"].lower()
    assert len(result["evidence"]) >= 2

def test_no_approval_means_no_execution():
    proposal = {"action": "example", "parameters": {}, "approval_status": "pending"}
    result = execute_if_approved(proposal, approved=False, simulate_action=True)
    assert result["execution_status"] == "not_executed"

def test_simulation_does_not_change_service():
    proposal = {"action": "example", "parameters": {}, "approval_status": "pending"}
    result = execute_if_approved(proposal, approved=True, simulate_action=True)
    assert result["execution_status"] == "simulated"
    assert "No service was changed" in result["execution_result"]["message"]
