# Incident Zero --- AI On-Call Engineer

## Detailed project README: problem, setup, work completed, issues, findings, and roadmap

> **Status as of 23 October 2026:** The OpenTelemetry Demo is running;
> the Incident Zero Python starter scaffold runs; its three existing
> tests pass; Prometheus is returning real metrics; and Jaeger's UI has
> been opened using its configured base path. We have inspected a slow
> checkout trace. The Python agent is **not yet connected to live
> telemetry**, the root cause is **not confirmed**, and real remediation
> is **not implemented**.

## Contents

1.  Problem statement
2.  Project goal and workflow
3.  Architecture
4.  Files created and inspected
5.  Environment and setup
6.  Work completed
7.  Live telemetry findings
8.  Issues encountered and how they were resolved
9.  Useful commands and PromQL
10. Current limitations
11. Remaining roadmap to ace the hackathon
12. Final demo checklist and presentation story

------------------------------------------------------------------------

## 1. Problem statement

The hackathon challenge is **"Incident Zero: Build an AI On-Call
Engineer."** The goal is to build an assistant that helps an engineer
investigate incidents across a distributed application. It should
collect observability evidence, identify likely causes, explain the
reasoning, recommend a safe action, require human approval before
changing anything, and verify whether an approved action improved the
system.

A credible system must do more than produce a plausible-sounding answer.
It should:

-   Collect real metrics and traces (and logs where available).
-   Connect symptoms across services and dependencies.
-   Separate confirmed observations from hypotheses.
-   Rank likely causes and explain the evidence for each.
-   Recommend a relevant, preferably reversible, remediation.
-   Require explicit human approval before state-changing actions.
-   Verify outcomes with fresh telemetry after an approved action.
-   Produce an auditable incident report.

The example environment is the **OpenTelemetry Demo**, a microservices
application with services including `frontend`, `frontend-proxy`,
`checkout`, `cart`, `product-catalog`, `payment`, and `currency`, plus
observability components such as Prometheus, Jaeger, and the
OpenTelemetry Collector.

### Incident being investigated

The current example is a slow/failing checkout flow. The trace evidence
so far includes a frontend checkout request returning HTTP `500`, a
proxy request returning `504` after about 15 seconds, a checkout
operation lasting roughly 2.8--2.9 minutes, and repeated slow
`ProductCatalogService/GetProduct` calls. This points to a possible
downstream bottleneck or timeout/retry issue, but the root cause is
**not confirmed**. The next step is to inspect span attributes/events
and compare failed and successful traces.

------------------------------------------------------------------------

## 2. Project goal and intended workflow

The intended Python agent workflow is:

1.  **Receive incident:** load incident details and affected service.
2.  **Collect evidence:** query Prometheus metrics and Jaeger traces.
3.  **Normalize evidence:** turn raw telemetry into consistent records.
4.  **Diagnose:** rank plausible causes using evidence, rules, and
    optionally an LLM.
5.  **Recommend:** propose a targeted action and explain its expected
    effect.
6.  **Approve:** stop and wait for explicit human approval.
7.  **Execute safely:** use only the official Action API and schema if
    supplied by the hackathon.
8.  **Verify:** query health and telemetry again after the approved
    action.
9.  **Report:** save evidence, hypothesis, confidence, approval,
    execution, and verification status.

**Safety rule:** do not restart containers, change flags, scale
services, or modify the demo automatically based only on a diagnosis.
The official Action API has not been provided in the material available
so far. Until its contract is known, remediation must remain a proposal
or simulation. Do not invent endpoints, action types, or payloads.

------------------------------------------------------------------------

## 3. Architecture

### Current environment

-   **OpenTelemetry Demo services:** generate traces and metrics.
-   **OpenTelemetry Collector:** receives/processes telemetry.
-   **Prometheus:** stores/query metrics, including OTLP-ingested
    metrics.
-   **Jaeger:** stores and displays distributed traces.
-   **Incident Zero Python scaffold:** runs an offline example workflow
    and creates a structured report. Its live telemetry integration
    remains future work.

### Intended data flow

``` text
OpenTelemetry Demo services
   |-- metrics / OTLP --> Collector / Prometheus
   |-- traces / OTLP ---> Jaeger
                              |
                              v
                    Incident Zero telemetry clients
                              |
                              v
                      Evidence normalization
                              |
                              v
                    Ranked diagnosis hypotheses
                              |
                              v
                   Proposed action + human approval
                              |
                              v
                    Official Action API, if provided
                              |
                              v
                    Post-action verification + report
```

We have manually queried Prometheus and inspected Jaeger traces. The
Python agent still uses bundled sample telemetry until live integration
is implemented.

------------------------------------------------------------------------

## 4. Files created and inspected

### Repository locations

OpenTelemetry Demo:

``` text
C:\Users\Tanmaya K\Hackathon\opentelemetry-demo
```

Incident Zero starter:

``` text
C:\Users\Tanmaya K\Hackathon\opentelemetry-demo\incident-zero-starter
```

### Relevant OpenTelemetry Demo files

``` text
opentelemetry-demo/
├── compose.yaml
├── compose.full.yaml
├── compose.observability.yaml
├── compose.extras.yaml
└── src/
    └── jaeger/
        ├── config.yml
        └── ui-config.json
```

The repository has many more files; this list highlights the Compose
files and Jaeger configuration relevant to our work.

### Incident Zero starter files

``` text
incident-zero-starter/
├── README.md
├── requirements.txt
├── .gitignore
├── app.py
├── agent.py
├── telemetry.py
├── diagnosis.py
├── remediation.py
├── action_client.py
├── verification.py
├── reporting.py
├── schemas.py
├── data/
│   ├── incidents/
│   │   └── checkout-timeout.json
│   └── sample_telemetry.json
├── tests/
│   └── test_diagnosis.py
└── reports/
    └── .gitkeep
```

### Purpose of each starter file

  ----------------------------------------------------------------------------
  File                                     Purpose
  ---------------------------------------- -----------------------------------
  `app.py`                                 Command-line entry point: loads an
                                           incident, runs the workflow,
                                           prints/saves the report.

  `agent.py`                               Orchestrates the incident-response
                                           stages.

  `telemetry.py`                           Telemetry boundary; currently uses
                                           bundled/offline example data.
                                           Extend it with real Prometheus and
                                           Jaeger clients.

  `diagnosis.py`                           Evaluates available evidence and
                                           produces a hypothesis. Current
                                           logic is simple/rule-based, not a
                                           proven root-cause engine.

  `remediation.py`                         Proposes remediation and tracks
                                           approval/execution state.

  `action_client.py`                       Intended integration boundary for
                                           the official Action API; real
                                           execution is not implemented.

  `verification.py`                        Intended post-action verification;
                                           it must query live health/telemetry
                                           in the completed version.

  `reporting.py`                           Writes a structured incident report
                                           to `reports/`.

  `schemas.py`                             Shared structures for incident,
                                           evidence, diagnosis, action, and
                                           report data.

  `data/incidents/checkout-timeout.json`   Practice incident input.

  `data/sample_telemetry.json`             Bundled example telemetry for
                                           offline execution.

  `tests/test_diagnosis.py`                Tests evidence-backed hypothesis
                                           generation, approval gating, and
                                           simulation safety.

  `requirements.txt`                       Python dependencies.

  `.gitignore`                             Excludes local/generated files from
                                           version control.

  `reports/.gitkeep`                       Keeps the reports folder in version
                                           control.
  ----------------------------------------------------------------------------

These descriptions summarize the starter's intended responsibilities.
Check the code itself as it evolves and update this README if the
implementation changes.

------------------------------------------------------------------------

## 5. Environment and setup

### Requirements

-   Windows and PowerShell.
-   Docker Desktop and Docker Compose.
-   OpenTelemetry Demo cloned locally.
-   Python 3.11 available through the `py` launcher.
-   Browser access to Prometheus and Jaeger.
-   Incident Zero starter extracted into the demo repository.

### Start the demo

Run from the demo root:

``` powershell
cd "C:\Users\Tanmaya K\Hackathon\opentelemetry-demo"
```

Validate the combined Compose configuration:

``` powershell
docker compose --env-file .env --env-file .env.override -f compose.yaml -f compose.full.yaml -f compose.observability.yaml -f compose.extras.yaml config --quiet
```

Start the services:

``` powershell
docker compose --env-file .env --env-file .env.override -f compose.yaml -f compose.full.yaml -f compose.observability.yaml -f compose.extras.yaml up --force-recreate --remove-orphans --detach
```

Check status:

``` powershell
docker compose --env-file .env --env-file .env.override -f compose.yaml -f compose.full.yaml -f compose.observability.yaml -f compose.extras.yaml ps
```

Use the same Compose files and environment arguments when running
Compose commands from the demo root. A bare
`docker compose logs prometheus` run from `incident-zero-starter`
returned `no such service: prometheus` because that subfolder does not
define the demo Compose services.

### Set up and run the Python starter

``` powershell
cd "C:\Users\Tanmaya K\Hackathon\opentelemetry-demo\incident-zero-starter"
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

The virtual environment was created and activation/dependency
installation worked.

Run the offline incident workflow:

``` powershell
python app.py --incident data/incidents/checkout-timeout.json
```

Run tests:

``` powershell
python -m pytest -v
```

Observed output:

``` text
Incident: practice-checkout-001
Diagnosis: Payment dependency connectivity or availability issue may be causing checkout failures.
Confidence: medium
Proposed action: investigate_payment_dependency
Approval: awaiting_approval
Execution: not_executed
Verification: not_run
Report: reports\practice-checkout-001-report.json
```

The test suite passed:

``` text
tests/test_diagnosis.py::test_sample_incident_produces_evidence_backed_hypothesis PASSED
tests/test_diagnosis.py::test_no_approval_means_no_execution PASSED
tests/test_diagnosis.py::test_simulation_does_not_change_service PASSED

3 passed
```

This proves only that the current offline scaffold and its three tests
work. The initial payment-dependency hypothesis came from sample
telemetry and is **not** a confirmed diagnosis of the live checkout
trace.

------------------------------------------------------------------------

## 6. Work completed so far

### 6.1 Demo environment

-   Cloned the OpenTelemetry Demo.
-   Validated and started it with the full Compose file set.
-   Checked service health and port mappings.
-   Found that some services, including `checkout` and
    `product-catalog`, were marked unhealthy during an earlier status
    check. Health can change; recheck it before the final demo.
-   Did not delete volumes or blindly change service configuration while
    diagnosing issues.

### 6.2 Python starter

-   Created/extracted `incident-zero-starter`.
-   Created and activated the Python environment.
-   Installed dependencies.
-   Ran the offline workflow and generated a report.
-   Ran all three existing tests successfully.
-   Confirmed that approval/execution/verification are not complete in
    the sample report.

### 6.3 Prometheus

The observed local endpoints were:

  -----------------------------------------------------------------------
  Component                           Address
  ----------------------------------- -----------------------------------
  Prometheus                          `http://localhost:9090`

  Jaeger UI/query port mapping        `http://localhost:63146` with the
                                      configured UI base path

  Collector OTLP/HTTP                 host port `55949`

  Collector OTLP/gRPC                 host port `55950`
  -----------------------------------------------------------------------

These came from the actual `docker compose ps` output. Host ports should
be rechecked if the stack is recreated.

Prometheus returned live data. An HTTP request-count metric showed
examples such as:

-   `cart` `AddItem`: 211 calls, status `200`.
-   `cart` `GetCart`: 995 calls, status `200`.
-   `ad` `GET /metrics`: 178 calls, status `200`.
-   `frontend`: 7,842 recorded HTTP requests in the returned series.

These are cumulative counter values, not requests per second.

The query

``` promql
count by (service_name) (http_server_request_duration_seconds_count)
```

returned these counts of metric series:

  Service        Series count
  ------------ --------------
  `cart`                    4
  `ad`                      1
  `frontend`                6
  `shipping`                3
  `jaeger`                  2

Checkout was absent from that particular HTTP request-count metric, but
it did have trace-derived metrics.

The query

``` promql
traces_span_metrics_calls_total{
  service_name="checkout",
  span_kind="SPAN_KIND_CLIENT",
  status_code="STATUS_CODE_ERROR"
}
```

returned `span_name="POST"` with value `7`. This is a cumulative count
of error-marked client spans in that series; it does not by itself
reveal the failed dependency or prove the root cause.

### 6.4 Jaeger

Jaeger's UI was eventually opened at:

``` text
http://localhost:63146/jaeger/ui/
```

The key configuration in `src/jaeger/config.yml` is:

``` yaml
extensions:
  jaeger_query:
    storage:
      traces: memory_backend
      metrics: metrics_backend
    base_path: /jaeger/ui
    ui:
      config_file: /etc/jaeger/ui-config.json
```

The configured `base_path: /jaeger/ui` explains why the root URL was not
the correct UI route.

------------------------------------------------------------------------

## 7. Live trace findings

### Trace list

Jaeger displayed examples including:

  Trace name                                 Spans   Errors   Duration
  ---------------------------------------- ------- -------- ----------
  `load-generator: user_checkout_single`        56        9    2.1 min
  `load-generator: user_checkout_multi`        128        7    3.0 min
  `load-generator: user_checkout_single`        65        7    2.6 min
  `load-generator: user_checkout_single`        81        8    3.0 min
  `load-generator: user_checkout_multi`        160        3    1.7 min
  `load-generator: user_checkout_multi`        191        3    1.8 min

Trace-level error totals aggregate spans across services. They are not
necessarily counts of failed customer checkouts.

### Detailed checkout trace

The trace excerpt showed:

  ------------------------------------------------------------------------------------------------
  Observation             Trace evidence                                   Interpretation
  ----------------------- ------------------------------------------------ -----------------------
  Proxy timeout           `frontend-proxy POST` returned `504` after about The proxy timed out
                          15.0 seconds                                     before the backend
                                                                           finished.

  Frontend error          `frontend POST /api/checkout` returned `500`     The checkout handler
                          after about 2.9 minutes                          eventually returned an
                                                                           internal server error.

  Slow checkout RPC       `checkout oteldemo.CheckoutService/PlaceOrder`   Backend order placement
                          took about 2.8 minutes                           is taking much too
                                                                           long.

  Slow helper             `prepareOrderItemsAndShippingQuoteFromCart` took Most of the elapsed
                          about 2.6 minutes                                time is inside this
                                                                           helper or its nested
                                                                           work.

  Slow catalog calls      `ProductCatalogService/GetProduct` spans         Product catalog is a
                          included about 38.0s, 30.8s, 27.8s, and 39.9s    strong lead to
                                                                           investigate.

  Database child spans    Examples ranged from about 1.2ms and 9.5ms to    These samples do not
                          3.7s                                             explain every long
                                                                           parent span. More
                                                                           attributes and traces
                                                                           are needed before
                                                                           ruling the database in
                                                                           or out.

  Possible request        A `checkout POST` span showed `408` near the end Inspect its
  timeout                 of the excerpt                                   attributes/events to
                                                                           determine its
                                                                           relationship to the
                                                                           other errors.
  ------------------------------------------------------------------------------------------------

### Current hypothesis---not confirmed root cause

Checkout's order preparation is being delayed by one or more downstream
operations. Repeated slow `ProductCatalogService/GetProduct` calls are a
leading candidate, and the frontend proxy's 15-second timeout happens
well before checkout completes. Retry behavior, timeout configuration,
or another operation within `prepareOrderItemsAndShippingQuoteFromCart`
could also contribute.

**Do not claim the product catalog is definitively the root cause yet.**
Inspect the slow span's RPC status, exception/event attributes,
retries/timeouts, and nested database spans. Compare with a successful
trace.

------------------------------------------------------------------------

## 8. Issues encountered and how we investigated them

### Issue A: The demo frontend initially showed an upstream timeout

Opening `http://127.0.0.1:8080/` initially produced an upstream request
timeout. Some services were unhealthy at that point.

**Response:** inspected container status and ports instead of deleting
volumes or blindly rebuilding everything. Later status output showed the
frontend and several services healthy. The exact original cause of the
first timeout was not conclusively established.

### Issue B: `no such service: prometheus`

A Compose command was run from `incident-zero-starter`, where the demo
services were not defined.

**Fix:** change to the demo root and use the complete Compose file list
and environment arguments.

### Issue C: Prometheus Targets said "No scrape pools found"

The Prometheus configuration at `/etc/prometheus/prometheus-config.yaml`
had `global` and `otlp` sections but no `scrape_configs`.

**What we learned:** the demo is ingesting metrics through OTLP, so an
empty Targets page can coexist with available metrics. We queried actual
metrics instead of blindly adding scrape targets. The scrape
configuration has not been changed.

### Issue D: Checkout had no `http_server_request_duration_seconds_count` series

The query
`http_server_request_duration_seconds_count{service_name="checkout"}`
returned no rows.

**What we learned:** checkout was absent from that metric family, not
from all telemetry. The metric `traces_span_metrics_calls_total`
returned checkout operations such as `CartService/GetCart`,
`CurrencyService/Convert`, `POST`, `PaymentService/Charge`, and
`ProductCatalogService/GetProduct`.

### Issue E: Jaeger returned 404 at `/`, `/status`, and `/api/v3/services`

**Cause found:** the Jaeger query extension is configured with
`base_path: /jaeger/ui`.

**Fix:** use `http://localhost:63146/jaeger/ui/`. The UI then displayed
traces.

### Issue F: Jaeger logs showed connection refused to `localhost:4317`

Jaeger logs showed attempts to export its own internal telemetry to
`127.0.0.1:4317` / `[::1]:4317`.

**Interpretation:** inside a container, `localhost` refers to that
container. The warnings indicate that Jaeger's internal telemetry
exporter could not connect at that address. They are separate from the
UI base-path issue and do not by themselves prove Jaeger's trace storage
or UI is broken. The UI and traces were subsequently accessible. These
internal export warnings have not been fixed.

### Issue G: The offline starter suggested a payment dependency issue

The starter output proposed `investigate_payment_dependency`.

**Important:** that result came from the bundled offline fixture and
current rule-based logic. It is not the confirmed live diagnosis. The
live trace currently points to slow checkout processing and slow
product-catalog calls as a lead, but the cause is still unconfirmed.

------------------------------------------------------------------------

## 9. Useful commands and queries

### Docker Compose status

Run from the demo root:

``` powershell
docker compose --env-file .env --env-file .env.override -f compose.yaml -f compose.full.yaml -f compose.observability.yaml -f compose.extras.yaml ps
```

### Prometheus logs

``` powershell
docker compose --env-file .env --env-file .env.override -f compose.yaml -f compose.full.yaml -f compose.observability.yaml -f compose.extras.yaml logs --tail 60 prometheus
```

### Read Prometheus configuration inside the container

``` powershell
docker compose --env-file .env --env-file .env.override -f compose.yaml -f compose.full.yaml -f compose.observability.yaml -f compose.extras.yaml exec prometheus cat /etc/prometheus/prometheus-config.yaml
```

### Read Jaeger configuration

``` powershell
Get-Content .\src\jaeger\config.yml
Get-ChildItem .\src\jaeger
```

### Inspect Jaeger startup command and mounts

``` powershell
docker inspect jaeger --format 'Entrypoint={{json .Config.Entrypoint}} Cmd={{json .Config.Cmd}} Mounts={{json .Mounts}}'
```

### Prometheus queries

All metric names:

``` promql
{__name__=~".+"}
```

HTTP request counts:

``` promql
http_server_request_duration_seconds_count
```

Series count by service:

``` promql
count by (service_name) (http_server_request_duration_seconds_count)
```

Checkout trace-derived calls:

``` promql
traces_span_metrics_calls_total{service_name="checkout"}
```

Checkout client-span errors:

``` promql
traces_span_metrics_calls_total{
  service_name="checkout",
  span_kind="SPAN_KIND_CLIENT",
  status_code="STATUS_CODE_ERROR"
}
```

Group errors by operation:

``` promql
sum by (span_name) (
  traces_span_metrics_calls_total{
    service_name="checkout",
    span_kind="SPAN_KIND_CLIENT",
    status_code="STATUS_CODE_ERROR"
  }
)
```

Group all client calls by operation:

``` promql
sum by (span_name) (
  traces_span_metrics_calls_total{
    service_name="checkout",
    span_kind="SPAN_KIND_CLIENT"
  }
)
```

### Run starter and tests

From `incident-zero-starter`:

``` powershell
python app.py --incident data/incidents/checkout-timeout.json
python -m pytest -v
```

------------------------------------------------------------------------

## 10. Current limitations

As of this README:

1.  The Python agent is **not yet connected to live Prometheus or
    Jaeger**. We have queried them manually.
2.  Diagnosis logic is simple/rule-based and has not yet ranked multiple
    live root-cause candidates.
3.  Root cause is unconfirmed. Slow product-catalog calls are a lead,
    not proof.
4.  `action_client.py` is a placeholder; real action execution is not
    implemented.
5.  Verification is not yet based on real before/after telemetry.
6.  The official Action API schema and expected report schema were not
    supplied in the material available during this work. Integrate the
    real contract when available; do not invent one.
7.  No automatic remediation has been demonstrated. The system should
    remain approval-gated.
8.  Jaeger internal telemetry export warnings remain unresolved, even
    though the UI works.
9.  Service health should be rechecked before the final demo.
10. The three existing tests cover the scaffold's current behaviors
    only, not the complete live workflow.

------------------------------------------------------------------------

## 11. Remaining roadmap to ace the hackathon

Complete the following in order.

### Phase 1 --- Stabilize and record the environment

-   [ ] Run `docker compose ... ps` from the demo root and save the
    output.
-   [ ] Confirm Prometheus at `http://localhost:9090`.
-   [ ] Confirm Jaeger at `http://localhost:63146/jaeger/ui/`.
-   [ ] Confirm the Collector is running.
-   [ ] Record any unhealthy service and inspect its logs.
-   [ ] Save a trace ID and incident time so the investigation is
    repeatable.
-   [ ] Avoid configuration changes that aren't backed by evidence.

**Deliverable:** repeatable environment and a known incident trace.

### Phase 2 --- Finish trace analysis

-   [ ] Open the slow `ProductCatalogService/GetProduct` span.
-   [ ] Record RPC status, exception attributes, events,
    retries/timeouts, and relevant child database span.
-   [ ] Inspect `PlaceOrder` and
    `prepareOrderItemsAndShippingQuoteFromCart`.
-   [ ] Determine whether slow catalog calls are sequential, retried, or
    blocked downstream.
-   [ ] Inspect the `408`, `500`, and `504` spans to establish their
    relationship.
-   [ ] Compare with a successful checkout trace.
-   [ ] Document confirmed facts, likely causes, and unknowns
    separately.

**Deliverable:** evidence table containing trace ID, span, service,
duration, status, and interpretation.

### Phase 3 --- Implement live Prometheus ingestion

In `telemetry.py`:

-   [ ] Query `http://localhost:9090/api/v1/query`.
-   [ ] Make the base URL configurable through environment variables.
-   [ ] Fetch current error and request metrics, plus suitable latency
    metrics when available.
-   [ ] Query `traces_span_metrics_calls_total` for
    service/operation/status breakdowns.
-   [ ] Add timeouts, error handling, and clear messages.
-   [ ] Handle missing labels, empty results, stale data, malformed
    responses, and Prometheus outages.
-   [ ] Mark evidence source and timestamp as live or fixture.
-   [ ] Keep the offline fixture for deterministic tests.
-   [ ] Add mocked-response unit tests.

**Deliverable:** the incident command fetches live metrics and records
them in the report.

### Phase 4 --- Implement Jaeger trace ingestion

-   [ ] Confirm the correct API path/version for the deployed Jaeger
    2.21.0 configuration.
-   [ ] Respect the configured `/jaeger/ui` base path; don't assume the
    root URL is the UI/API base.
-   [ ] Add a trace-query function.
-   [ ] Retrieve relevant traces for the service and incident time
    window.
-   [ ] Extract span names, hierarchy, durations, statuses, attributes,
    and exceptions.
-   [ ] Correlate metrics and traces using service, time window,
    operation, and trace IDs where possible.
-   [ ] Handle missing traces/API errors without crashing the agent.

**Deliverable:** the Python agent fetches trace evidence
programmatically.

### Phase 5 --- Improve diagnosis quality

-   [ ] Rank multiple candidate causes rather than returning one canned
    answer.
-   [ ] Link every claim to specific telemetry.
-   [ ] Include confidence, counter-evidence, and alternatives.
-   [ ] Distinguish service unhealthy, dependency slow, request timed
    out, and telemetry missing.
-   [ ] Compare failing and successful traces.
-   [ ] Do not infer root cause from one counter or one trace.
-   [ ] Mark root cause "unconfirmed" until evidence is sufficient.
-   [ ] Recommend the next best investigation when evidence is
    incomplete.

**Deliverable:** a transparent, evidence-backed diagnosis.

### Phase 6 --- Add safe action proposals and approval

-   [ ] Obtain the official Action API specification if it is provided.
-   [ ] Implement only documented actions and payloads.
-   [ ] Validate action names and parameters against an allowlist.
-   [ ] Require explicit human approval before state-changing calls.
-   [ ] Record proposed action, approval decision, time, and result.
-   [ ] Keep dry-run/simulation as the default.
-   [ ] Prove that missing or denied approval prevents execution.
-   [ ] Never invent API endpoints or secrets.

**Deliverable:** auditable action handling that follows the real
hackathon contract.

### Phase 7 --- Implement live verification

-   [ ] Capture baseline health/error/latency before the action.
-   [ ] After an approved action, wait for a bounded verification
    window.
-   [ ] Re-query the same signals and compare against baseline.
-   [ ] Check service health and relevant error/latency changes.
-   [ ] Report success, failure, or inconclusive honestly.
-   [ ] Do not call an incident "fixed" just because an action API
    returned success.

**Deliverable:** measurable before/after verification.

### Phase 8 --- Improve report and CLI

-   [ ] Generate a readable Markdown summary and structured JSON report.
-   [ ] Include incident metadata, evidence sources, timestamps,
    queries, trace IDs, ranked hypotheses, confidence, proposed action,
    approval, execution, and verification.
-   [ ] Separate known, suspected, and unknown facts.
-   [ ] Add a CLI option for live versus fixture mode.
-   [ ] Configure endpoints with environment variables.
-   [ ] Keep secrets out of reports and logs.

**Deliverable:** polished, auditable incident report.

### Phase 9 --- Testing

-   [ ] Keep all three existing tests passing.
-   [ ] Test Prometheus success/failure and empty results.
-   [ ] Test malformed responses, timeouts, and stale evidence.
-   [ ] Test diagnosis ranking and evidence attribution.
-   [ ] Test no execution without approval.
-   [ ] Test action failure and verification failure.
-   [ ] Add an integration test against the running demo if time allows.
-   [ ] Ensure missing telemetry never causes a fabricated diagnosis.

**Deliverable:** repeatable tests for safety and reliability.

### Phase 10 --- Presentation polish

-   [ ] Confirm judging criteria, API contract, expected output schema,
    and time limits.
-   [ ] Prepare an architecture diagram and a clean setup guide.
-   [ ] Demonstrate a real metric and trace leading to a diagnosis.
-   [ ] Show evidence, confidence, and alternatives.
-   [ ] Demonstrate that denied approval prevents execution.
-   [ ] If the official Action API is available, demonstrate an allowed
    action and verification; otherwise label it clearly as simulated.
-   [ ] Prepare a 2--3 minute demo and backup screenshots/report in case
    a service fails.
-   [ ] State limitations honestly and show the roadmap.

**Deliverable:** a reproducible end-to-end demo, not merely a dashboard
or sample output.

------------------------------------------------------------------------

## 12. Final demo checklist

-   [ ] Environment is running and status recorded.
-   [ ] Incident is reproducible or represented by a saved
    trace/fixture.
-   [ ] Agent retrieves real metrics and traces.
-   [ ] Diagnosis claims are linked to evidence.
-   [ ] Facts are separated from hypotheses.
-   [ ] Proposed action and expected effect are explained.
-   [ ] No action executes without explicit approval.
-   [ ] Action uses the official API contract if supplied.
-   [ ] Verification uses fresh telemetry and can report inconclusive.
-   [ ] Structured report is saved.
-   [ ] Tests cover safety and failure cases.
-   [ ] Setup commands work from a clean terminal.
-   [ ] No secrets are committed or logged.
-   [ ] Presentation distinguishes implemented features from simulation.

## Suggested demo story

1.  "A checkout flow is taking minutes, and users are receiving
    gateway/server errors."
2.  Show Prometheus trace-derived checkout client errors.
3.  Open the trace: proxy `504` at around 15 seconds, frontend checkout
    `500` after around 2.9 minutes, and checkout `PlaceOrder` taking
    around 2.8 minutes.
4.  Follow the dependency spans and investigate slow
    `ProductCatalogService/GetProduct` calls.
5.  Present an evidence-backed hypothesis, confidence, alternatives, and
    what remains unknown.
6.  Recommend a safe action and explain its expected impact.
7.  Demonstrate that no action occurs without approval.
8.  If the official action path is implemented, execute an approved
    action and verify with fresh telemetry; otherwise label the step as
    simulation.
9.  Show the structured report.

Do not claim product catalog is definitively the root cause until the
span attributes and comparative evidence support that conclusion. Do not
claim remediation or verification succeeded unless it actually did.

------------------------------------------------------------------------

## Final status summary

**Completed:** OpenTelemetry Demo launched with all currently running
services healthy; Incident Zero starter created and run; six tests passed;
Prometheus metrics queried live; Jaeger UI opened through its configured
base path; a slow checkout trace inspected; the agent now records live
error, request, and latency queries with timestamps and collection errors.

**In progress:** determine why product-catalog calls are slow; connect
Jaeger programmatically to the Python agent; produce a ranked live
diagnosis.

**Not completed yet:** confirmed root cause, Jaeger trace ingestion,
official Action API integration, real action execution, post-action
verification, and a complete end-to-end hackathon demo.

**Recommended immediate next task:** inspect the attributes/events on
the slow `ProductCatalogService/GetProduct` span and compare it with a
successful trace. Then implement the Prometheus client in `telemetry.py`
while keeping the offline fixture and approval-safety tests intact.
