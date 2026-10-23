"""Read-only telemetry adapters for Incident Zero.

Live mode currently queries the local Prometheus HTTP API. No API key is
needed for the user's current local demo configuration. Jaeger integration
will be added only after its configured query API is verified.
"""
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

    if payload.get("status") != "success":
        raise TelemetryError(
            f"Prometheus returned status={payload.get('status')}: "
            f"{payload.get('error', 'unknown query error')}"
        )
    return payload.get("data", {}).get("result", [])


def collect_prometheus_telemetry(incident):
    """Collect current checkout client-span metrics from Prometheus."""
    base_url = os.getenv("PROMETHEUS_URL", DEFAULT_PROMETHEUS_URL)
    query = (
        'sum by (service_name, span_name, status_code, span_kind) '
        '(traces_span_metrics_calls_total{service_name="checkout",'
        'span_kind="SPAN_KIND_CLIENT"})'
    )
    rows = _prometheus_query(base_url, query)
    metrics = []
    for row in rows:
        labels = row.get("metric", {})
        value_pair = row.get("value", [None, None])
        try:
            value = float(value_pair[1])
        except (TypeError, ValueError, IndexError):
            continue
        metrics.append({
            "name": "traces_span_metrics_calls_total",
            "service": labels.get("service_name", "unknown"),
            "operation": labels.get("span_name", "unknown"),
            "span_kind": labels.get("span_kind", "unknown"),
            "status_code": labels.get("status_code", "unknown"),
            "value": value,
        })

    return {
        "source": "prometheus_live",
        "source_url": base_url,
        "collected_at_utc": datetime.now(timezone.utc).isoformat(),
        "logs": [],
        "metrics": metrics,
        "traces": [],
        "deployment_events": [],
        "affected_services": incident.get("affected_services", []),
        "queries": [query],
        "collection_errors": [],
        "notes": [
            "Metrics were fetched live from Prometheus.",
            "Prometheus counters are cumulative, not rates.",
            "Trace details and logs are not yet fetched programmatically."
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
