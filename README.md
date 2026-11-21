# Assignment 1 – NYC Taxi Batch ETL

Local batch pipeline: download NYC Yellow Taxi data → clean (Python) →
load a PostgreSQL star schema → business metrics dashboard (Streamlit),
orchestrated with Dagster.

## Architecture
bronze (raw parquet, data/raw) → silver (cleaned parquet, data/silver) → gold (Postgres `gold` schema) → SQL views → Streamlit

<img width="3676" height="3697" alt="assignment 1" src="https://github.com/user-attachments/assets/bd6f7fea-9a8f-43b3-a72b-586288346237" />

| Layer | Tech | Code |
|---|---|---|
| Setup | Bash, Docker, curl | `setup.sh`, `docker-compose.yml` |
| Data model | PostgreSQL star schema | `gold.fact_trip` + `dim_date`, `dim_location`, `dim_payment_type`, `dim_vendor`, `dim_rate_code` |
| ETL | Python / pandas | `etl/transform.py`, `etl/load.py` |
| Orchestration | Dagster (monthly partitions, retries, schedule, failure sensor) | `orchestration/` |
| Logging | structlog JSON logs → `logs/pipeline.log`, alerts → `logs/alerts.log` | `etl/logging_config.py` |
| Metrics | SQL views | `sql/analytics_queries.sql` |
| Dashboard | Streamlit + Plotly | `dashboard/app.py` |

## How to run
    ./setup.sh                                   # venv, deps, Postgres, downloads data
    source .venv/bin/activate
    export DAGSTER_HOME=$PWD/.dagster_home && mkdir -p $DAGSTER_HOME
    dagster dev -m orchestration.definitions     # UI: http://localhost:3000 -> materialize assets
    docker exec -i nyc_taxi_postgres psql -U taxi -d taxi_dw < sql/analytics_queries.sql
    streamlit run dashboard/app.py               # http://localhost:8501

## Assumptions
- Data: Q3 2026 (Jul–Sep), the latest complete quarter (TLC publishes with ~2-month delay).
- Cleaning: duplicates removed; only trips whose pickup and dropoff fall in the file's year;
  duration 1 min–6 h; distance 0.01–200 miles; negative fare/total treated as refunds and removed.
- Nulls: rate code → 99 (Unknown, per TLC dictionary); surcharges/fees → 0;
  passenger_count left NULL (not invented).
- Unknown/invalid codes map to the dimension's "Unknown" member so no trip is lost.
- Taxi zones (dim_location) are static reference data, loaded once at setup.
- Reloads are idempotent: each month is deleted and re-inserted (COPY) in one transaction, keyed by `source_month`.
- Single Postgres container and local Dagster are enough for this scale; failure alerts write to a log file
