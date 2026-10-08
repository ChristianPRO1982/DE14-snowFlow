-- Le mois traité ne doit contenir aucun trajet en double.
SELECT COUNT(*) = COUNT(DISTINCT trip_sk)
FROM NYC_TAXI.MARTS.FCT_TRIPS
WHERE source_file_month = '{{ ds }}'::date;