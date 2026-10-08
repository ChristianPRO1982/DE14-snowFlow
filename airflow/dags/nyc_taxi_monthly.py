import pendulum
import requests
from pathlib import Path
from airflow.providers.snowflake.hooks.snowflake import SnowflakeHook
from airflow.sdk import dag, get_current_context, task

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

    file_name = build_file_name()
    url = check_file_exists(file_name)
    staged_file = download_and_put(url)
    copy_into_raw(staged_file)


nyc_taxi_monthly()
