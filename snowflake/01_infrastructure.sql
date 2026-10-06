-- ============================================================
-- 1. Role used by ingestion and transformation tools
-- ============================================================

USE ROLE USERADMIN;

CREATE ROLE IF NOT EXISTS TRANSFORMER
    COMMENT = 'Role used by NYC Taxi ingestion and transformation tools';

GRANT ROLE TRANSFORMER TO ROLE SYSADMIN;


-- ============================================================
-- 2. Compute warehouse
-- ============================================================

USE ROLE SYSADMIN;

CREATE WAREHOUSE IF NOT EXISTS NYC_TAXI_WH
  WAREHOUSE_SIZE = 'XSMALL'
  AUTO_SUSPEND = 60
  AUTO_RESUME = TRUE
  INITIALLY_SUSPENDED = TRUE;


  -- ============================================================
-- 3. Database and schemas
-- ============================================================

USE ROLE SYSADMIN;

CREATE DATABASE IF NOT EXISTS NYC_TAXI;

CREATE SCHEMA IF NOT EXISTS NYC_TAXI.RAW;
CREATE SCHEMA IF NOT EXISTS NYC_TAXI.STAGING;
CREATE SCHEMA IF NOT EXISTS NYC_TAXI.INTERMEDIATE;
CREATE SCHEMA IF NOT EXISTS NYC_TAXI.MARTS;


-- ============================================================
-- 4. Privileges for the tool role
-- ============================================================

USE ROLE SYSADMIN;

GRANT USAGE, OPERATE
  ON WAREHOUSE NYC_TAXI_WH
  TO ROLE TRANSFORMER;

GRANT USAGE
  ON DATABASE NYC_TAXI
  TO ROLE TRANSFORMER;

GRANT USAGE, CREATE TABLE, CREATE STAGE, CREATE FILE FORMAT
  ON SCHEMA NYC_TAXI.RAW
  TO ROLE TRANSFORMER;

GRANT USAGE, CREATE TABLE, CREATE VIEW
  ON SCHEMA NYC_TAXI.STAGING
  TO ROLE TRANSFORMER;

GRANT USAGE, CREATE TABLE, CREATE VIEW
  ON SCHEMA NYC_TAXI.INTERMEDIATE
  TO ROLE TRANSFORMER;

GRANT USAGE, CREATE TABLE, CREATE VIEW
  ON SCHEMA NYC_TAXI.MARTS
  TO ROLE TRANSFORMER;


-- ============================================================
-- 5. Service user
-- ============================================================

USE ROLE USERADMIN;

CREATE USER IF NOT EXISTS AIRFLOW_SVC
  TYPE = SERVICE
  DEFAULT_ROLE = TRANSFORMER
  DEFAULT_WAREHOUSE = NYC_TAXI_WH
  DEFAULT_NAMESPACE = NYC_TAXI.RAW
  RSA_PUBLIC_KEY = '<TA_CLE_PUBLIQUE_COMPLETE>'
  COMMENT = 'Service account used by Airflow for NYC Taxi pipeline';

GRANT ROLE TRANSFORMER TO USER AIRFLOW_SVC;