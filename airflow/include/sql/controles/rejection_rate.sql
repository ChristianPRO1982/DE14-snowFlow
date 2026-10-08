-- Le pourcentage de trajets rejetés du mois doit rester sous le seuil autorisé.
SELECT
    COALESCE(
        100.0 * COUNT_IF(rejection_reason IS NOT NULL)
        / NULLIF(COUNT(*), 0),
        100.0
    ) <= {{ params.max_rejection_pct }}
FROM NYC_TAXI.INTERMEDIATE.INT_TRIPS__FLAGGED
WHERE source_file_month = '{{ ds }}'::date;