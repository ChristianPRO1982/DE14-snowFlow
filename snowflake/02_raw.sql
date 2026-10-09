-- ============================================================
-- RAW layer objects
-- ============================================================

USE ROLE TRANSFORMER;
USE WAREHOUSE NYC_TAXI_WH;
USE DATABASE NYC_TAXI;
USE SCHEMA RAW;

-- ============================================================
-- File formats
-- ============================================================

CREATE OR REPLACE FILE FORMAT PARQUET_FF
  TYPE = PARQUET
  USE_LOGICAL_TYPE = TRUE;

CREATE OR REPLACE FILE FORMAT CSV_FF
  TYPE = CSV
  PARSE_HEADER = TRUE
  FIELD_OPTIONALLY_ENCLOSED_BY = '"'
  ERROR_ON_COLUMN_COUNT_MISMATCH = FALSE;

-- ============================================================
-- Internal stage
-- ============================================================

CREATE STAGE IF NOT EXISTS NYC_TAXI_STAGE
  COMMENT = 'Internal stage for NYC Taxi source files';

-- ============================================================
-- RAW tables
-- ============================================================

CREATE TABLE IF NOT EXISTS YELLOW_TRIPDATA (
    vendorid               NUMBER,
    tpep_pickup_datetime   TIMESTAMP_NTZ,
    tpep_dropoff_datetime  TIMESTAMP_NTZ,
    passenger_count        NUMBER,
    trip_distance          FLOAT,
    ratecodeid             NUMBER,
    store_and_fwd_flag     VARCHAR,
    pulocationid           NUMBER,
    dolocationid           NUMBER,
    payment_type           NUMBER,
    fare_amount            FLOAT,
    extra                  FLOAT,
    mta_tax                FLOAT,
    tip_amount             FLOAT,
    tolls_amount           FLOAT,
    improvement_surcharge  FLOAT,
    total_amount           FLOAT,
    congestion_surcharge   FLOAT,
    airport_fee            FLOAT,
    cbd_congestion_fee     FLOAT,
    _source_file           VARCHAR,
    _loaded_at             TIMESTAMP_NTZ
);

CREATE TABLE IF NOT EXISTS TAXI_ZONE_LOOKUP (
    locationid    NUMBER,
    borough       VARCHAR,
    zone          VARCHAR,
    service_zone  VARCHAR,
    _source_file  VARCHAR,
    _loaded_at    TIMESTAMP_NTZ
);