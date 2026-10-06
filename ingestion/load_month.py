import re
import sys
from pathlib import Path
import requests

MONTH_PATTERN = re.compile(r"^\d{4}-(0[1-9]|1[0-2])$")
BASE_URL = "https://d37ci6vzurychx.cloudfront.net/trip-data"
DOWNLOAD_DIR = Path("parquet")
CHUNK_SIZE = 8 * 1024 * 1024


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
    file_path = download_file(url, file_name)

    print(f"Downloaded to: {file_path}")
    print(f"Month selected: {month}")
    print(f"File name: {file_name}")
    print(f"Source URL: {url}")


if __name__ == "__main__":
    main()