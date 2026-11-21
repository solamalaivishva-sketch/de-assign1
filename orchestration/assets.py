"""The pipeline steps: bronze -> silver -> gold, one partition per month."""
import pandas as pd
from dagster import (AssetExecutionContext, MaterializeResult,
                     MonthlyPartitionsDefinition, RetryPolicy, asset)

from etl.config import RAW_DIR, SILVER_DIR
from etl.logging_config import log_asset
from etl.load import load_fact
from etl.transform import build_fact, clean_trips

# One partition per monthly file: 2023-01, 2023-02 (end_date is exclusive)
monthly = MonthlyPartitionsDefinition(start_date="2026-07-01", end_date="2026-10-01")
retry = RetryPolicy(max_retries=2, delay=10)   # retry transient failures (e.g. DB restart)


def month_of(context: AssetExecutionContext) -> str:
    return context.partition_key[:7]           





@asset(group_name="bronze", partitions_def=monthly)
@log_asset
def bronze_trips(context: AssetExecutionContext) -> MaterializeResult:
    """Raw parquet file downloaded by setup.sh (never modified)."""
    path = RAW_DIR / f"yellow_tripdata_{month_of(context)}.parquet"
    if not path.exists():
        raise FileNotFoundError(f"{path} missing - run ./setup.sh first")
    return MaterializeResult(metadata={"size_mb": round(path.stat().st_size / 1e6, 1)})


@asset(group_name="silver", partitions_def=monthly, deps=[bronze_trips], retry_policy=retry)
@log_asset
def silver_trips(context: AssetExecutionContext) -> MaterializeResult:
    """Clean the raw trips, add dimension keys, save as parquet."""
    month = month_of(context)
    raw = pd.read_parquet(RAW_DIR / f"yellow_tripdata_{month}.parquet")
    fact = build_fact(clean_trips(raw, month), month)
    SILVER_DIR.mkdir(parents=True, exist_ok=True)
    fact.to_parquet(SILVER_DIR / f"trips_{month}.parquet", index=False)
    return MaterializeResult(metadata={
        "rows_in": len(raw), "rows_out": len(fact), "rows_rejected": len(raw) - len(fact),
    })


@asset(group_name="gold", partitions_def=monthly, deps=[silver_trips],
       retry_policy=retry)
@log_asset
def fact_taxi_trips(context: AssetExecutionContext) -> MaterializeResult:
    """Load the month's silver data into dw.fact_taxi_trips."""
    month = month_of(context)
    fact = pd.read_parquet(SILVER_DIR / f"trips_{month}.parquet")
    loaded = load_fact(fact, month)
    if loaded != len(fact):                    # reconciliation check
        raise ValueError(f"Loaded {loaded} rows but silver has {len(fact)}")
    return MaterializeResult(metadata={"rows_in": len(fact), "rows_out": loaded})