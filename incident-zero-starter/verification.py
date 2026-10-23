def verify_recovery(before, after, diagnosis):
    """Never claim recovery without fresh post-action telemetry."""
    if after is None:
        return {
            "status": "inconclusive",
            "details": "Simulation did not change the system and no fresh telemetry was collected."
        }
    return {
        "status": "inconclusive",
        "details": "Define recovery thresholds and compare fresh telemetry before claiming recovery."
    }
