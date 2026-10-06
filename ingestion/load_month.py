import re
import sys
from pathlib import Path
import requests
import os
import snowflake.connector
from cryptography.hazmat.primitives import serialization

MONTH_PATTERN = re.compile(r"^\d{4}-(0[1-9]|1[0-2])$")
BASE_URL = "https://d37ci6vzurychx.cloudfront.net/trip-data"
DOWNLOAD_DIR = Path("parquet")
CHUNK_SIZE = 8 * 1024 * 1024


def copy_into_raw(conn, file_name: str) -> list[tuple]:
    with conn.cursor() as cur:
        cur.execute(
            f"""
            COPY INTO YELLOW_TRIPDATA
            FROM @NYC_TAXI_STAGE
            FILES = ('{file_name}')
            FILE_FORMAT = (FORMAT_NAME = PARQUET_FF)
            MATCH_BY_COLUMN_NAME = CASE_INSENSITIVE
            INCLUDE_METADATA = (
                _source_file = METADATA$FILENAME,
                _loaded_at = METADATA$START_SCAN_TIME
            )
            ON_ERROR = ABORT_STATEMENT
            """
        )

        return cur.fetchall()


def upload_to_stage(conn, file_path: Path) -> list[tuple]:
    with conn.cursor() as cur:
        cur.execute(
            f"""
            PUT file://{file_path.resolve()}
            @NYC_TAXI_STAGE
            AUTO_COMPRESS=FALSE
            OVERWRITE=FALSE
            """
        )

        return cur.fetchall()


def load_private_key() -> object:
    key_path = Path(os.environ["SNOWFLAKE_PRIVATE_KEY_PATH"])

    with key_path.open("rb") as key_file:
        return serialization.load_pem_private_key(
            key_file.read(),
            password=None,
        )


def create_snowflake_connection():
    private_key = load_private_key()

    return snowflake.connector.connect(
        account=os.environ["SNOWFLAKE_ACCOUNT"],
        user=os.environ["SNOWFLAKE_USER"],
        private_key=private_key,
        role=os.environ["SNOWFLAKE_ROLE"],
        warehouse=os.environ["SNOWFLAKE_WAREHOUSE"],
        database=os.environ["SNOWFLAKE_DATABASE"],
        schema=os.environ["SNOWFLAKE_SCHEMA"],
    )


def download_file(url: str, file_name: str) -> Path:
    DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)
    destination = DOWNLOAD_DIR / file_name

    with requests.get(url, stream=True, timeout=120) as response:
        response.raise_for_status()

        with destination.open("wb") as file:
            for chunk in response.iter_content(chunk_size=CHUNK_SIZE):
                if chunk:
                    file.write(chunk)

    return destination


def build_file_name(month: str) -> str:
    return f"yellow_tripdata_{month}.parquet"


def build_url(month: str) -> str:
    file_name = build_file_name(month)
    return f"{BASE_URL}/{file_name}"


def validate_month(month: str) -> str:
    if not MONTH_PATTERN.fullmatch(month):
        raise ValueError(
            "Month must use the YYYY-MM format, for example: 2025-01"
        )

    return month


def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit(
            "Usage: python3 load_month.py YYYY-MM"
        )

    month = validate_month(sys.argv[1])
    file_name = build_file_name(month)
    url = build_url(month)

    print(f"Month selected: {month}")
    print(f"File name: {file_name}")
    print(f"Source URL: {url}")

    file_path = download_file(url, file_name)
    print(f"Downloaded to: {file_path}")

    with create_snowflake_connection() as conn:
        with conn.cursor() as cur:
            result = cur.execute(
                """
                SELECT
                    CURRENT_USER(),
                    CURRENT_ROLE(),
                    CURRENT_WAREHOUSE(),
                    CURRENT_DATABASE(),
                    CURRENT_SCHEMA()
                """
            ).fetchone()

            print(f"Snowflake connection: {result}")

        upload_results = upload_to_stage(conn, file_path)

        for row in upload_results:
            print(f"PUT result: {row}")

        copy_results = copy_into_raw(conn, file_name)

        for row in copy_results:
            print(f"COPY result: {row}")


if __name__ == "__main__":
    main()