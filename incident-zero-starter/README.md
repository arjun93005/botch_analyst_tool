# Incident Zero — Starter Kit

This is a beginner-friendly Python scaffold for the Bosch Incident Zero project.

## What works
- Loads a sample incident.
- Reads bundled example logs, metrics and traces.
- Produces an evidence-backed baseline diagnosis.
- Proposes a remediation without executing it automatically.
- Requires explicit `--approve` before any action simulation.
- Writes a JSON report to `reports/`.
- Includes tests.

## Important
This is a starter scaffold, not a finished submission. It currently uses offline example telemetry. It does NOT connect to live Grafana/Prometheus/Jaeger or the Bosch Action API. The simulated action does not change Docker or any service. Before real integration, use the actual event documentation and required output schema. Do not guess API endpoints.

## Run on Windows PowerShell
```powershell
cd incident-zero-starter
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python app.py --incident data/incidents/checkout-timeout.json
```

This first run creates a report and does not execute a repair.

Test the approval path in simulation-only mode:
```powershell
python app.py --incident data/incidents/checkout-timeout.json --approve --simulate-action
```

Run tests:
```powershell
python -m pytest
```

## Files
- `app.py`: command-line entry point
- `agent.py`: end-to-end workflow
- `telemetry.py`: offline telemetry adapter to replace with real read-only queries
- `diagnosis.py`: baseline diagnosis logic
- `remediation.py`: proposal and approval gate
- `action_client.py`: safe placeholder for the official Action API
- `verification.py`: recovery verification placeholder
- `reporting.py`: JSON report writer
- `data/`: sample incident and telemetry
- `tests/`: basic safety tests

## Next tasks
1. Update report fields to match the event's exact JSON schema.
2. Connect telemetry adapters to the actual endpoints documented for the demo.
3. Implement only permitted Action API operations from the official docs.
4. Bind human approval to the exact proposed action.
5. Verify recovery using fresh post-action telemetry and documented thresholds.
6. Test every practice incident and use the official evaluator.


## Live Prometheus mode (read-only)

The starter now supports a live Prometheus query. This does **not** need an API key in the current local demo configuration.

From the `incident-zero-starter` folder, with the virtual environment active:

```powershell
python app.py --incident data/incidents/checkout-timeout.json --telemetry-mode prometheus
```

By default it queries `http://localhost:9090`. To override the URL:

```powershell
$env:PROMETHEUS_URL = "http://localhost:9090"
python app.py --incident data/incidents/checkout-timeout.json --telemetry-mode prometheus
```

The live mode queries affected-service error counters from
`traces_span_metrics_calls_total`, HTTP request counters from
`http_server_request_duration_seconds_count`, and a five-minute 95th
percentile latency query from the corresponding histogram. It records every
query, collection timestamp, source URL, and per-query collection error in the
JSON report. Missing series are treated as missing evidence rather than
healthy results. It does not yet fetch Jaeger traces or logs, and it does not
execute remediation. A low-confidence result is expected when metrics alone
do not establish the cause.

The request timeout is configurable:

```powershell
$env:PROMETHEUS_TIMEOUT_SECONDS = "5"
```

The offline fixture remains the default so existing tests stay deterministic:

```powershell
python app.py --incident data/incidents/checkout-timeout.json
```

### API distinction

- Prometheus HTTP API: used now for read-only metrics.
- Jaeger query API: next integration stage, after verifying the query path supported by the configured Jaeger version.
- Hackathon Action API: required only for real remediation; do not implement until the official endpoint/schema and allowed actions are supplied.
