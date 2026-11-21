"""Failure alert: runs whenever any pipeline run fails."""
import json
from datetime import datetime, timezone

from dagster import DefaultSensorStatus, RunFailureSensorContext, run_failure_sensor

from etl.config import LOG_DIR
from etl.logging_config import log


@run_failure_sensor(default_status=DefaultSensorStatus.RUNNING)
def alert_on_failure(context: RunFailureSensorContext):
    alert = {
        "ts": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "job": context.dagster_run.job_name,
        "run_id": context.dagster_run.run_id,
        "partition": context.dagster_run.tags.get("dagster/partition"),
        "error": context.failure_event.message,
    }
    log.error("pipeline_run_failed", **alert)
    with open(LOG_DIR / "alerts.log", "a") as f:
        f.write(json.dumps(alert) + "\n")
 