import json
from pathlib import Path
from unittest.mock import patch

from telemetry import TelemetryError, collect_telemetry, collect_prometheus_telemetry
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


def test_prometheus_collection_records_error_request_and_latency_metrics():
    incident = {"affected_services": ["checkout"]}

    def query(_base_url, promql, timeout):
        assert timeout == 2.5
        if "traces_span_metrics_calls_total" in promql:
            return [{"metric": {
                "service_name": "checkout",
                "span_name": "payment",
                "status_code": "STATUS_CODE_ERROR",
            }, "value": ["1", "3"]}]
        if "histogram_quantile" in promql:
            return [{"metric": {"service_name": "checkout"}, "value": ["1", "0.42"]}]
        return [{"metric": {
            "service_name": "checkout",
            "http_route": "/checkout",
            "http_response_status_code": "500",
        }, "value": ["1", "8"]}]

    with patch.dict("os.environ", {"PROMETHEUS_TIMEOUT_SECONDS": "2.5"}):
        with patch("telemetry._prometheus_query", side_effect=query):
            result = collect_prometheus_telemetry(incident)

    assert result["source"] == "prometheus_live"
    assert len(result["queries"]) == 3
    assert {metric["metric_type"] for metric in result["metrics"]} == {
        "error", "request", "latency"
    }
    assert result["collection_errors"] == []


def test_prometheus_collection_keeps_partial_results_when_query_fails():
    incident = {"affected_services": ["checkout"]}

    with patch("telemetry._prometheus_query", side_effect=[
        [{"metric": {"service_name": "checkout"}, "value": ["1", "4"]}],
        TelemetryError("Prometheus unavailable"),
        [],
    ]):
        result = collect_prometheus_telemetry(incident)

    assert len(result["metrics"]) == 1
    assert len(result["collection_errors"]) == 1
    assert "Prometheus unavailable" in result["collection_errors"][0]["error"]


def test_prometheus_query_rejects_malformed_success_payload():
    with patch("telemetry.urlopen") as urlopen:
        response = urlopen.return_value.__enter__.return_value
        response.read.return_value = b'{"status": "success", "data": {}}'
        with patch.dict("os.environ", {}, clear=False):
            try:
                from telemetry import _prometheus_query
                _prometheus_query("http://prometheus", "up")
            except TelemetryError as exc:
                assert "malformed" in str(exc)
            else:
                raise AssertionError("Malformed Prometheus data should fail clearly")
