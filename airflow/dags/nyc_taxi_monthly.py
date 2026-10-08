from pathlib import Path

import pendulum
import requests
from airflow.providers.common.sql.operators.sql import SQLExecuteQueryOperator
from airflow.providers.snowflake.hooks.snowflake import SnowflakeHook
from airflow.sdk import TaskGroup, dag, get_current_context, task

BASE_URL = "https://d37ci6vzurychx.cloudfront.net/trip-data"
CONN_ID = "snowflake_nyc_taxi"
STAGE = "NYC_TAXI.RAW.NYC_TAXI_STAGE"


@dag(
    dag_id="nyc_taxi_monthly",
    schedule="@monthly",
    start_date=pendulum.datetime(2025, 1, 1, tz="UTC"),
    end_date=pendulum.datetime(2025, 3, 1, tz="UTC"),
    catchup=True,
    max_active_runs=1,
    template_searchpath="/usr/local/airflow/include/sql",
    params={
        "max_trip_distance_miles": 100,
        "max_trip_duration_min": 180,
        "start_month": "2025-01-01",
        "end_month": "2025-04-01",
    },
)
def nyc_taxi_monthly():

    @task
    def build_file_name() -> str:
        context = get_current_context()
        month = context["data_interval_start"].strftime("%Y-%m")
        file_name = f"yellow_tripdata_{month}.parquet"

        print(f"Logical month: {month}")
        print(f"File name: {file_name}")

        return file_name

    @task
    def check_file_exists(file_name: str) -> str:
        url = f"{BASE_URL}/{file_name}"

        response = requests.head(url, timeout=30)
        response.raise_for_status()

        print(f"File available: {url}")

        return url

    @task
    def download_and_put(url: str) -> str:
        file_name = url.rsplit("/", 1)[-1]
        destination = Path("/tmp") / file_name

        try:
            with requests.get(url, stream=True, timeout=120) as response:
                response.raise_for_status()

                with destination.open("wb") as file:
                    for chunk in response.iter_content(
                        chunk_size=8 * 1024 * 1024
                    ):
                        if chunk:
                            file.write(chunk)

            hook = SnowflakeHook(snowflake_conn_id=CONN_ID)

            hook.run(
                f"""
                PUT file://{destination}
                @{STAGE}
                AUTO_COMPRESS=FALSE
                OVERWRITE=FALSE
                """
            )

            print(f"Uploaded to stage: {file_name}")

            return file_name

        finally:
            destination.unlink(missing_ok=True)

    @task
    def copy_into_raw(file_name: str) -> None:
        hook = SnowflakeHook(snowflake_conn_id=CONN_ID)

        hook.run(
            f"""
            COPY INTO NYC_TAXI.RAW.YELLOW_TRIPDATA
            FROM @{STAGE}
            FILES = ('{file_name}')
            FILE_FORMAT = (
                FORMAT_NAME = NYC_TAXI.RAW.PARQUET_FF
            )
            MATCH_BY_COLUMN_NAME = CASE_INSENSITIVE
            INCLUDE_METADATA = (
                _source_file = METADATA$FILENAME,
                _loaded_at = METADATA$START_SCAN_TIME
            )
            ON_ERROR = ABORT_STATEMENT
            """
        )

        print(f"Copied into RAW: {file_name}")

    # ------------------------------------------------------------------
    # RAW ingestion
    # ------------------------------------------------------------------

    file_name = build_file_name()
    url = check_file_exists(file_name)
    staged_file = download_and_put(url)
    raw_loaded = copy_into_raw(staged_file)

    # ------------------------------------------------------------------
    # Core tables
    # ------------------------------------------------------------------

    create_core_tables = SQLExecuteQueryOperator(
        task_id="create_core_tables",
        conn_id=CONN_ID,
        sql="00_tables.sql",
        split_statements=True,
    )

    # ------------------------------------------------------------------
    # STAGING
    # ------------------------------------------------------------------

    with TaskGroup(group_id="staging"):

        stg_yellow_trips = SQLExecuteQueryOperator(
            task_id="stg_tlc__yellow_trips",
            conn_id=CONN_ID,
            sql="staging/stg_tlc__yellow_trips.sql",
            split_statements=True,
        )

        stg_taxi_zones = SQLExecuteQueryOperator(
            task_id="stg_tlc__taxi_zones",
            conn_id=CONN_ID,
            sql="staging/stg_tlc__taxi_zones.sql",
            split_statements=True,
        )

        codes_tlc = SQLExecuteQueryOperator(
            task_id="codes_tlc",
            conn_id=CONN_ID,
            sql="staging/codes_tlc.sql",
            split_statements=True,
        )

    # ------------------------------------------------------------------
    # INTERMEDIATE
    # ------------------------------------------------------------------

    with TaskGroup(group_id="intermediate"):

        int_trips_flagged = SQLExecuteQueryOperator(
            task_id="int_trips__flagged",
            conn_id=CONN_ID,
            sql="intermediate/int_trips__flagged.sql",
            split_statements=True,
        )

        int_trips_enriched = SQLExecuteQueryOperator(
            task_id="int_trips__enriched",
            conn_id=CONN_ID,
            sql="intermediate/int_trips__enriched.sql",
            split_statements=True,
        )

        int_trips_flagged >> int_trips_enriched

    # ------------------------------------------------------------------
    # MARTS
    # ------------------------------------------------------------------

    with TaskGroup(group_id="marts"):

        dim_date = SQLExecuteQueryOperator(
            task_id="dim_date",
            conn_id=CONN_ID,
            sql="marts/dim_date.sql",
            split_statements=True,
        )

        dim_payment_type = SQLExecuteQueryOperator(
            task_id="dim_payment_type",
            conn_id=CONN_ID,
            sql="marts/dim_payment_type.sql",
            split_statements=True,
        )

        dim_rate_code = SQLExecuteQueryOperator(
            task_id="dim_rate_code",
            conn_id=CONN_ID,
            sql="marts/dim_rate_code.sql",
            split_statements=True,
        )

        dim_vendor = SQLExecuteQueryOperator(
            task_id="dim_vendor",
            conn_id=CONN_ID,
            sql="marts/dim_vendor.sql",
            split_statements=True,
        )

        dim_zone = SQLExecuteQueryOperator(
            task_id="dim_zone",
            conn_id=CONN_ID,
            sql="marts/dim_zone.sql",
            split_statements=True,
        )

        fct_trips = SQLExecuteQueryOperator(
            task_id="fct_trips",
            conn_id=CONN_ID,
            sql="marts/fct_trips.sql",
            split_statements=True,
        )

        mart_daily_revenue = SQLExecuteQueryOperator(
            task_id="mart_daily_revenue",
            conn_id=CONN_ID,
            sql="marts/mart_daily_revenue.sql",
            split_statements=True,
        )

        mart_data_quality = SQLExecuteQueryOperator(
            task_id="mart_data_quality",
            conn_id=CONN_ID,
            sql="marts/mart_data_quality.sql",
            split_statements=True,
        )

        mart_zone_hourly_demand = SQLExecuteQueryOperator(
            task_id="mart_zone_hourly_demand",
            conn_id=CONN_ID,
            sql="marts/mart_zone_hourly_demand.sql",
            split_statements=True,
        )

    # ------------------------------------------------------------------
    # Dependencies
    # ------------------------------------------------------------------

    raw_loaded >> create_core_tables

    create_core_tables >> [
        stg_yellow_trips,
        stg_taxi_zones,
        codes_tlc,
        dim_date,
    ]

    stg_yellow_trips >> int_trips_flagged
    int_trips_enriched >> fct_trips

    stg_taxi_zones >> dim_zone

    codes_tlc >> [
        dim_vendor,
        dim_payment_type,
        dim_rate_code,
    ]

    int_trips_flagged >> mart_data_quality

    [
        fct_trips,
        dim_date,
        dim_payment_type,
    ] >> mart_daily_revenue

    [
        fct_trips,
        dim_zone,
    ] >> mart_zone_hourly_demand


nyc_taxi_monthly()