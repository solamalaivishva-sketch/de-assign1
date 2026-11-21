#SILVER: clean raw trips and add the star-schema keys.
import pandas as pd


def clean_trips(df: pd.DataFrame, month: str) -> pd.DataFrame:
    """Remove bad trips. month = 'YYYY-MM'."""
    year = int(month[:4])
    df = df.copy()
    df.columns = df.columns.str.lower()                 # Airport_fee vs airport_fee
    df = df.drop_duplicates()

    pickup = pd.to_datetime(df["tpep_pickup_datetime"], errors="coerce")
    dropoff = pd.to_datetime(df["tpep_dropoff_datetime"], errors="coerce")
    minutes = (dropoff - pickup).dt.total_seconds() / 60

    keep = (
        (pickup.dt.year == year) & (dropoff.dt.year == year)   # correct year only
        & minutes.between(1, 360)                               # 1 min .. 6 hours
        & df["trip_distance"].between(0.01, 200)                # no zero distance
        & (df["fare_amount"] >= 0) & (df["total_amount"] >= 0)  # no refunds
    )
    df = df[keep].copy()
    df["trip_duration_minutes"] = minutes[keep].round(2)
    return df.fillna({"ratecodeid": 99, "congestion_surcharge": 0, "airport_fee": 0})


def build_fact(df: pd.DataFrame, month: str) -> pd.DataFrame:
    """Shape cleaned trips into the gold.fact_trip columns and derive the keys."""
    pickup = df["tpep_pickup_datetime"]

    def to_key(column, valid_codes, unknown):
        """Missing or unexpected codes -> the dimension's 'Unknown' row."""
        codes = pd.to_numeric(df[column], errors="coerce").fillna(unknown).astype(int)
        return codes.where(codes.isin(valid_codes), unknown)

    def money(column):
        """Amount columns are NOT NULL in gold.fact_trip: missing -> 0."""
        if column not in df:                       # e.g. cbd_congestion_fee before 2025
            return 0.0
        return pd.to_numeric(df[column], errors="coerce").fillna(0).round(2)

    return pd.DataFrame({
        "pickup_datetime": pickup,
        "dropoff_datetime": df["tpep_dropoff_datetime"],
        "passenger_count": pd.to_numeric(df["passenger_count"], errors="coerce").astype("Int64"),
        "trip_distance": df["trip_distance"].round(2),
        "fare_amount": money("fare_amount"),
        "extra": money("extra"),
        "mta_tax": money("mta_tax"),
        "tip_amount": money("tip_amount"),
        "tolls_amount": money("tolls_amount"),
        "improvement_surcharge": money("improvement_surcharge"),
        "total_amount": money("total_amount"),
        "congestion_surcharge": money("congestion_surcharge"),
        "airport_fee": money("airport_fee"),
        "cbd_congestion_fee": money("cbd_congestion_fee"),
        # keys -> dimension tables
        "payment_type_id": to_key("payment_type", range(0, 7), 0),
        "vendor_id": to_key("vendorid", [1, 2, 6, 7], 0),
        "rate_code_id": to_key("ratecodeid", [1, 2, 3, 4, 5, 6, 99], 99),
        "pickup_location_id": to_key("pulocationid", range(1, 266), 264),
        "dropoff_location_id": to_key("dolocationid", range(1, 266), 264),
        "date_key": pickup.dt.strftime("%Y%m%d").astype(int),      # dim_date
        # lineage: which monthly file the row came from (for safe reloads)
        "source_month": month,
    })