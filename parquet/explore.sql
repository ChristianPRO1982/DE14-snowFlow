SELECT
  COUNT(*) AS row_count
FROM read_parquet('yellow_tripdata_2025-01.parquet');

DESCRIBE
SELECT *
FROM read_parquet('yellow_tripdata_2025-01.parquet');

SELECT *
FROM read_parquet('yellow_tripdata_2025-01.parquet')
LIMIT 10;
