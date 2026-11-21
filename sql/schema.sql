CREATE SCHEMA IF NOT EXISTS gold;
SET search_path = gold;

-- Dimensions Tables Creation
CREATE TABLE IF NOT EXISTS dim_date (
    date_key INTEGER PRIMARY KEY,
    full_date DATE NOT NULL UNIQUE,
    year INT NOT NULL,
    month INT NOT NULL,
    day INT NOT NULL,
    quarter INT NOT NULL
);

CREATE TABLE IF NOT EXISTS dim_location (
    location_key INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    location_id INT NOT NULL UNIQUE,
    borough VARCHAR(50) NOT NULL,
    zone VARCHAR(100) NOT NULL,
    service_zone VARCHAR(50) NOT NULL
);

CREATE TABLE IF NOT EXISTS dim_payment_type (
    payment_type_key INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    payment_type_id INT NOT NULL UNIQUE,
    payment_type_name VARCHAR(50) NOT NULL
);

CREATE TABLE IF NOT EXISTS dim_vendor (
    vendor_key INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    vendor_id INT NOT NULL UNIQUE,
    vendor_name VARCHAR(100) NOT NULL
);

CREATE TABLE IF NOT EXISTS dim_rate_code (

    rate_code_key   INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    rate_code_id    INT NOT NULL UNIQUE,
    rate_code_name  VARCHAR(40) NOT NULL
);


-- fact table Creation
CREATE TABLE IF NOT EXISTS fact_trip (
    trip_key INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    pickup_datetime TIMESTAMP NOT NULL,
    dropoff_datetime TIMESTAMP NOT NULL,
    passenger_count INT NOT NULL,
    trip_distance FLOAT NOT NULL,
    fare_amount FLOAT NOT NULL,
    extra FLOAT NOT NULL,
    mta_tax FLOAT NOT NULL,
    tip_amount FLOAT NOT NULL,
    tolls_amount FLOAT NOT NULL,
    improvement_surcharge FLOAT NOT NULL,
    total_amount FLOAT NOT NULL,
    congestion_surcharge FLOAT NOT NULL,
    Airport_fee FLOAT NOT NULL,
    cbd_congestion_fee FLOAT NOT NULL,
    request_source VARCHAR(50) NULL,
    payment_type_id INT NOT NULL REFERENCES dim_payment_type(payment_type_id),
    vendor_id INT NOT NULL REFERENCES dim_vendor(vendor_id),
    rate_code_id INT NOT NULL REFERENCES dim_rate_code(rate_code_id),
    pickup_location_id INT NOT NULL REFERENCES dim_location(location_id),
    dropoff_location_id INT NOT NULL REFERENCES dim_location(location_id),
    date_key INT NOT NULL REFERENCES dim_date(date_key),
    loaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);


-- Indexes for fact table
CREATE INDEX idx_fact_trip_pickup_datetime ON fact_trip(pickup_datetime);
CREATE INDEX idx_fact_trip_dropoff_datetime ON fact_trip(dropoff_datetime);
CREATE INDEX idx_fact_trip_payment_type_id ON fact_trip(payment_type_id);
CREATE INDEX idx_fact_trip_pickup_location_id ON fact_trip(pickup_location_id);
CREATE INDEX idx_fact_trip_dropoff_location_id ON fact_trip(dropoff_location_id);



-- Pipeline audit table 

CREATE TABLE IF NOT EXISTS etl_run_audit (
    pipeline_id     BIGSERIAL PRIMARY KEY,
    pipeline_name   VARCHAR(64) NOT NULL,
    source_month    CHAR(7),
    started_at      TIMESTAMP NOT NULL,
    finished_at     TIMESTAMP,
    rows_in         BIGINT,
    rows_out        BIGINT,
    rows_rejected   BIGINT,
    status          VARCHAR(16) NOT NULL,   
    error_message   TEXT
);




-- Data feeding for dim tables used dictonary values from NYC site

INSERT INTO dim_payment_type(payment_type_id, payment_type_name) VALUES
    (0, 'Flex Fare / Unknown'),
    (1, 'Credit card'),
    (2, 'Cash'),
    (3, 'No charge'),
    (4, 'Dispute'),
    (5, 'Unknown'),
    (6, 'Voided trip');


INSERT INTO dim_rate_code(rate_code_id, rate_code_name) VALUES
    (1,  'Standard rate'),
    (2,  'JFK'),
    (3,  'Newark'),
    (4,  'Nassau or Westchester'),
    (5,  'Negotiated fare'),
    (6,  'Group ride'),
    (99, 'Unknown');

INSERT INTO dim_vendor(vendor_id, vendor_name) VALUES
    (1, 'Creative Mobile Technologies, LLC'),
    (2, 'Curb Mobility, LLC'),
    (6, 'Myle Technologies Inc'),
    (7, 'Helix');

    
COPY gold.dim_location (location_id, borough, zone, service_zone)
FROM '/data/taxi_zone_lookup.csv'
WITH (FORMAT csv, HEADER true); 

INSERT INTO dim_date  
SELECT to_char(date, 'YYYYMMDD')::int AS date_key,
       date AS full_date,
       EXTRACT(YEAR FROM date) AS year,
       EXTRACT(MONTH FROM date) AS month,
       EXTRACT(DAY FROM date) AS day,
       EXTRACT(QUARTER FROM date) AS quarter
FROM generate_series('2026-01-01'::date, '2030-01-01'::date, '1 day'::interval) AS date;