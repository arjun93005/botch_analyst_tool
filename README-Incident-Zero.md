# Incident Zero - Phase 1

## Stabilize and record the environment

This repository snapshot contains the Incident Zero Phase 1 environment
record. Later investigation and implementation work remains available in the
local workspace but is intentionally not included in this branch.

## Project goal

Incident Zero is an AI on-call engineer for the OpenTelemetry Demo. The
planned system will collect observability evidence, separate facts from
hypotheses, recommend safe actions, require explicit approval, and verify
outcomes.

Phase 1 establishes a repeatable environment and records the known incident
context without making unsupported configuration changes.

## Environment

The OpenTelemetry Demo is a microservices application with services including
`frontend`, `frontend-proxy`, `checkout`, `cart`, `product-catalog`, `payment`,
and `currency`. Its observability components include Prometheus, Jaeger, and
the OpenTelemetry Collector.

The local workspace is:

```text
C:\Users\Tanmaya K\Hackathon\opentelemetry-demo
```

## Phase 1 verification

The following environment checks were completed:

- The Docker Compose demo stack was started from the repository root.
- `checkout` and `product-catalog` recovered to healthy status.
- Prometheus was confirmed ready at `http://localhost:9090`.
- Jaeger was confirmed at `http://localhost:63146/jaeger/ui/`.
- The OpenTelemetry Collector was running.
- The configured Jaeger base path was confirmed from
  `src/jaeger/config.yml`.
- A repeatable checkout incident context and time window were recorded.

Observed endpoint mappings can change when the stack is recreated. Recheck
them with Docker Compose before a later demonstration.

## Known incident context

The example incident is a slow and failing checkout flow. The recorded
incident window is:

```text
2026-10-23T10:00:00Z to 2026-10-23T10:10:00Z
```

The affected services are `checkout` and `payment`. The initial evidence
describes checkout errors and apparent timeouts while calling payment.

This document records environment stabilization only. It does not claim a
confirmed root cause or authorize any remediation.

## Repeatable commands

From the repository root:

```powershell
docker compose -f compose.yaml -f compose.observability.yaml ps
```

Check Prometheus:

```powershell
Invoke-WebRequest -UseBasicParsing http://localhost:9090/-/ready
```

Open Jaeger:

```text
http://localhost:63146/jaeger/ui/
```

## Phase 1 deliverable

The Phase 1 deliverable is a repeatable local environment with documented
service status, observability endpoints, and a known incident time window.

Phase 2 trace analysis and Phase 3 live telemetry ingestion are intentionally
not part of this repository branch.
