import json
from pathlib import Path
from datetime import datetime, timezone

def write_report(report, report_dir):
    report_dir.mkdir(parents=True, exist_ok=True)
    safe_id = "".join(c if c.isalnum() or c in "-_" else "_" for c in report["incident_id"])
    path = report_dir / f"{safe_id}-report.json"
    output = dict(report)
    output["generated_at_utc"] = datetime.now(timezone.utc).isoformat()
    path.write_text(json.dumps(output, indent=2), encoding="utf-8")
    return path
