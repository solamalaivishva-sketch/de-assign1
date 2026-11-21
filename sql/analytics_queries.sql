
-- 1. Average fare amount per mile

CREATE OR REPLACE VIEW gold.vw_fare_per_mile AS
SELECT
    f.source_month,
    COUNT(*)                                                   AS trips,
    ROUND(SUM(f.fare_amount)::numeric, 2)                      AS total_fare,
    ROUND(SUM(f.trip_distance)::numeric, 2)                    AS total_miles,
    ROUND((SUM(f.fare_amount) / NULLIF(SUM(f.trip_distance), 0))::numeric, 2)
                                                               AS avg_fare_per_mile
FROM gold.fact_trip f
GROUP BY f.source_month;

-- 2. Peak hours for taxi rides (trips per pickup hour)
CREATE OR REPLACE VIEW gold.vw_trips_by_hour AS
SELECT
    f.source_month,
    EXTRACT(HOUR FROM f.pickup_datetime)::int                  AS pickup_hour,
    COUNT(*)                                                   AS trips,
    ROUND(AVG(f.total_amount)::numeric, 2)                     AS avg_total_amount
FROM gold.fact_trip f
GROUP BY f.source_month, EXTRACT(HOUR FROM f.pickup_datetime);

-- 3. Total revenue by payment type (joins the payment-type dimension)
CREATE OR REPLACE VIEW gold.vw_revenue_by_payment AS
SELECT
    f.source_month,
    p.payment_type_name,
    COUNT(*)                                                   AS trips,
    ROUND(SUM(f.total_amount)::numeric, 2)                     AS total_revenue
FROM gold.fact_trip f
JOIN gold.dim_payment_type p ON p.payment_type_id = f.payment_type_id
GROUP BY f.source_month, p.payment_type_name;

