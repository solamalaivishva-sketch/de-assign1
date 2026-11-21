#single-page Streamlit dashboard on the gold views.


import sys
from pathlib import Path

import pandas as pd
import plotly.express as px
import psycopg2
import streamlit as st

sys.path.append(str(Path(__file__).resolve().parents[1]))   # so `etl` can be imported
from etl.config import PG_DSN  # noqa: E402

st.set_page_config(page_title="NYC Taxi Dashboard", layout="wide")


@st.cache_data(ttl=600)   # cache query results for 10 minutes
def query(sql: str) -> pd.DataFrame:
    with psycopg2.connect(PG_DSN) as conn, conn.cursor() as cur:
        cur.execute(sql)
        columns = [c.name for c in cur.description]
        return pd.DataFrame(cur.fetchall(), columns=columns)


fare = query("SELECT * FROM gold.vw_fare_per_mile ORDER BY source_month")
hours = query("SELECT * FROM gold.vw_trips_by_hour")
payment = query("SELECT * FROM gold.vw_revenue_by_payment")

# ---------- month filter ----------
st.title("NYC Yellow Taxi Dashboard")
months = st.multiselect("Months", fare["source_month"].tolist(),
                        default=fare["source_month"].tolist())
if not months:
    st.warning("Select at least one month.")
    st.stop()
fare = fare[fare["source_month"].isin(months)]
hours = hours[hours["source_month"].isin(months)]
payment = payment[payment["source_month"].isin(months)]

# ---------- KPI row ----------
total_trips = int(fare["trips"].sum())
total_revenue = float(payment["total_revenue"].sum())
fare_per_mile = float(fare["total_fare"].sum()) / float(fare["total_miles"].sum())

k1, k2, k3 = st.columns(3)
k1.metric("Total trips", f"{total_trips:,}")
k2.metric("Total revenue", f"${total_revenue:,.0f}")
k3.metric("Average fare per mile", f"${fare_per_mile:,.2f}")

# ---------- charts ----------
left, right = st.columns(2)

by_hour = hours.groupby("pickup_hour", as_index=False)["trips"].sum()
peak = by_hour.loc[by_hour["trips"].idxmax()]
left.subheader("Peak hours")
left.caption(f"Busiest hour: {int(peak.pickup_hour):02d}:00 with {int(peak.trips):,} trips")
left.plotly_chart(
    px.bar(by_hour, x="pickup_hour", y="trips",
           labels={"pickup_hour": "Pickup hour", "trips": "Trips"}),
    width="stretch",
)

by_payment = (payment.groupby("payment_type_name", as_index=False)["total_revenue"].sum()
              .sort_values("total_revenue", ascending=False))
right.subheader("Revenue by payment type")
right.plotly_chart(
    px.bar(by_payment, x="payment_type_name", y="total_revenue",
           labels={"payment_type_name": "Payment type", "total_revenue": "Revenue ($)"}),
    width="stretch",
)

st.subheader("Average fare per mile by month")
st.dataframe(fare[["source_month", "trips", "total_fare", "total_miles", "avg_fare_per_mile"]],
             hide_index=True, width="stretch")