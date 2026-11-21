"""GOLD: load dimensions and facts into the Postgres star schema."""
import io

import pandas as pd
import psycopg2

from etl.config import PG_DSN





def load_fact(fact: pd.DataFrame, month: str) -> int:
    """Replace one month (like Databricks replaceWhere): DELETE + COPY in one transaction."""
    csv = io.StringIO()
    fact.to_csv(csv, index=False, header=False)
    csv.seek(0)
    with psycopg2.connect(PG_DSN) as conn, conn.cursor() as cur:   # commit or rollback
        cur.execute("DELETE FROM gold.fact_trip WHERE source_month = %s", (month,))
        cur.copy_expert(
            f"COPY gold.fact_trip ({', '.join(fact.columns)}) FROM STDIN WITH CSV", csv
        )
        return cur.rowcount