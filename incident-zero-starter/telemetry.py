"""Read-only telemetry adapters for Incident Zero."""
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

DATA_PATH = Path(__file__).parent / "data" / "sample_telemetry.json"
DEFAULT_PROMETHEUS_URL = "http://localhost:9090"


class TelemetryError(RuntimeError):
    """Raised when a telemetry source cannot be queried."""


def _prometheus_query(base_url, promql, timeout=5):
    """Run a read-only instant query against Prometheus's HTTP API."""
    url = base_url.rstrip("/") + "/api/v1/query?" + urlencode({"query": promql})
    request = Request(url, headers={"Accept": "application/json"}, method="GET")
    try:
        with urlopen(request, timeout=timeout) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except (HTTPError, URLError, TimeoutError, json.JSONDecodeError) as exc:
        raise TelemetryError(f"Prometheus query failed: {exc}") from exc

    if not isinstance(payload, dict):
        raise TelemetryError("Prometheus returned a non-object JSON payload")
    if payload.get("status") != "success":
        raise TelemetryError(
            f"Prometheus returned status={payload.get('status')}: "
            f"{payload.get('error', 'unknown query error')}"
        )
    data = payload.get("data")
    results = data.get("result") if isinstance(data, dict) else None
    if not isinstance(results, list):
        raise TelemetryError("Prometheus returned a malformed result payload")
    return results


def _query_timeout():
    raw_timeout = os.getenv("PROMETHEUS_TIMEOUT_SECONDS", "5")
    try:
        timeout = float(raw_timeout)
    except ValueError as exc:
        raise TelemetryError(
            f"PROMETHEUS_TIMEOUT_SECONDS must be a positive number, got {raw_timeout!r}"
        ) from exc
    if timeout <= 0:
        raise TelemetryError("PROMETHEUS_TIMEOUT_SECONDS must be greater than zero")
    return timeout


def _metric_rows(rows, name, metric_type, default_service=None):
    metrics = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        labels = row.get("metric")
        value_pair = row.get("value")
        if not isinstance(labels, dict) or not isinstance(value_pair, list) or len(value_pair) < 2:
            continue
        try:
            value = float(value_pair[1])
        except (TypeError, ValueError):
            continue
        metrics.append({
            "name": name,
            "metric_type": metric_type,
            "service": labels.get("service_name", default_service or "unknown"),
            "operation": labels.get("span_name") or labels.get("http_route", "unknown"),
            "status_code": labels.get("status_code")
                or labels.get("http_response_status_code", "unknown"),
            "span_kind": labels.get("span_kind", "unknown"),
            "value": value,
            "labels": labels,
        })
    return metrics


def collect_prometheus_telemetry(incident):
    """Collect current error, request, and latency metrics from Prometheus."""
    base_url = os.getenv("PROMETHEUS_URL", DEFAULT_PROMETHEUS_URL)
    timeout = _query_timeout()
    services = incident.get("affected_services") or ["checkout"]
    query_specs = []
    for service in services:
        escaped_service = service.replace("\\", "\\\\").replace('"', '\\"')
        query_specs.extend([
            (
                "traces_span_metrics_calls_total",
                "error",
                service,
                f'sum by (service_name, span_name, status_code, span_kind) '
                f'(traces_span_metrics_calls_total{{service_name="{escaped_service}",'
                'status_code="STATUS_CODE_ERROR"})',
            ),
            (
                "http_server_request_duration_seconds_count",
                "request",
                service,
                f'sum by (service_name, http_route, http_response_status_code) '
                f'(http_server_request_duration_seconds_count{{service_name="{escaped_service}"}})',
            ),
            (
                "http_server_request_duration_seconds",
                "latency",
                service,
                f'histogram_quantile(0.95, sum by (service_name, le) '
                f'(rate(http_server_request_duration_seconds_bucket{{service_name="{escaped_service}"}}[5m])))',
            ),
        ])

    metrics = []
    queries = []
    collection_errors = []
    for name, metric_type, service, query in query_specs:
        queries.append(query)
        try:
            rows = _prometheus_query(base_url, query, timeout=timeout)
        except TelemetryError as exc:
            collection_errors.append({"query": query, "error": str(exc)})
            continue
        metrics.extend(_metric_rows(rows, name, metric_type, default_service=service))

    return {
        "source": "prometheus_live",
        "source_url": base_url,
        "collected_at_utc": datetime.now(timezone.utc).isoformat(),
        "logs": [],
        "metrics": metrics,
        "traces": [],
        "deployment_events": [],
        "affected_services": incident.get("affected_services", []),
        "queries": queries,
        "collection_errors": collection_errors,
        "notes": [
            "Metrics were fetched live from Prometheus.",
            "Prometheus counters are cumulative, not rates.",
            "Latency is a five-minute 95th percentile when histogram data is available.",
            "Empty or invalid series are recorded as missing evidence."
        ],
    }


def collect_telemetry(incident, mode=None):
    """Collect live Prometheus data or the deterministic offline fixture.

    mode values: "prometheus" or "fixture". If omitted, fixture mode is kept
    as the default so existing tests and offline runs remain deterministic.
    """
    mode = (mode or os.getenv("INCIDENT_ZERO_TELEMETRY_MODE", "fixture")).lower()
    if mode in {"prometheus", "live", "live-prometheus"}:
        return collect_prometheus_telemetry(incident)
    if mode != "fixture":
        raise ValueError(f"Unknown telemetry mode: {mode!r}. Use 'fixture' or 'prometheus'.")

    payload = json.loads(DATA_PATH.read_text(encoding="utf-8"))
    return {
        "source": "bundled_offline_fixture",
        "logs": payload.get("logs", []),
        "metrics": payload.get("metrics", []),
        "traces": payload.get("traces", []),
        "deployment_events": payload.get("deployment_events", []),
        "affected_services": incident.get("affected_services", []),
        "collection_errors": [],
        "notes": ["Using bundled example telemetry; no live API was queried."]
    }
