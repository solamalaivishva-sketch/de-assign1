"""Entry point Dagster loads"""
from dagster import Definitions, build_schedule_from_partitioned_job, define_asset_job

from orchestration.alerts import alert_on_failure
from orchestration.assets import (bronze_trips, fact_taxi_trips,
                                  monthly, silver_trips)

# Job: the monthly bronze -> silver -> gold run
taxi_job = define_asset_job("monthly_taxi_etl",
                            selection=[bronze_trips, silver_trips, fact_taxi_trips],
                            partitions_def=monthly)

# Schedule: run each month's partition at 02:00 after the month ends
monthly_schedule = build_schedule_from_partitioned_job(taxi_job, hour_of_day=2)

defs = Definitions(
    assets=[bronze_trips, silver_trips, fact_taxi_trips],
    jobs=[taxi_job],
    schedules=[monthly_schedule],
    sensors=[alert_on_failure],
)