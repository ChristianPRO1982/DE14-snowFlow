from pathlib import Path
import os
import snowflake.connector
from cryptography.hazmat.primitives import serialization
import requests


ZONE_URL = "https://d37ci6vzurychx.cloudfront.net/misc/taxi_zone_lookup.csv"
DOWNLOAD_DIR = Path("csv")
FILE_NAME = "taxi_zone_lookup.csv"
CHUNK_SIZE = 1024 * 1024


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


def download_file() -> Path:
    DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)
    destination = DOWNLOAD_DIR / FILE_NAME

    with requests.get(ZONE_URL, stream=True, timeout=120) as response:
        response.raise_for_status()

        with destination.open("wb") as file:
            for chunk in response.iter_content(chunk_size=CHUNK_SIZE):
                if chunk:
                    file.write(chunk)

    return destination


def main() -> None:
    file_path = download_file()
    print(f"Downloaded to: {file_path}")

    with create_snowflake_connection() as conn:
        upload_results = upload_to_stage(conn, file_path)

        for row in upload_results:
            print(f"PUT result: {row}")


if __name__ == "__main__":
    main()