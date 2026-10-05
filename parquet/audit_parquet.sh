#!/usr/bin/env bash

clear

set -euo pipefail

FILE="${1:-yellow_tripdata_2025-01.parquet}"
DUCKDB_SERVICE="${DUCKDB_SERVICE:-duckdb}"

SOURCE_URL="https://d37ci6vzurychx.cloudfront.net/trip-data/$(basename "$FILE")"

if [[ ! -f "$FILE" ]]; then
    echo "ERREUR : fichier introuvable : $FILE"
    exit 1
fi

section() {
    echo
    echo "============================================================"
    echo "$1"
    echo "============================================================"
}

duckdb_query() {
    docker compose run --rm "$DUCKDB_SERVICE" -c "$1"
}


# -------------------------------------------------------------------
# 1. IDENTITÉ DE LA SOURCE
# -------------------------------------------------------------------

section "1 - IDENTITÉ DE LA SOURCE"

echo "Nom              : NYC Yellow Taxi Trip Records"
echo "Producteur       : NYC Taxi & Limousine Commission (TLC)"
echo "URL              : $SOURCE_URL"
echo "Accès            : public, sans authentification"
echo "Format           : Parquet"
echo "Fréquence        : mensuelle"
echo "Délai publication: à compléter depuis la documentation TLC"


# -------------------------------------------------------------------
# 2. VOLUME RÉEL
# -------------------------------------------------------------------

section "2 - VOLUME DU FICHIER"

echo "Fichier : $FILE"
echo "Taille lisible : $(du -h "$FILE" | cut -f1)"
echo "Taille en octets : $(stat -c '%s' "$FILE")"

echo
echo "--- Nombre de lignes ---"

duckdb_query "
SELECT COUNT(*) AS row_count
FROM read_parquet('$FILE');
"

echo
echo "--- Nombre de colonnes ---"

duckdb_query "
SELECT COUNT(*) AS column_count
FROM parquet_schema('$FILE')
WHERE type IS NOT NULL;
"


# -------------------------------------------------------------------
# 3. SCHÉMA DU PARQUET
# -------------------------------------------------------------------

section "3 - COLONNES ET TYPES DU FICHIER"

duckdb_query "
SELECT
    name AS column_name,
    type AS parquet_type,
    logical_type
FROM parquet_schema('$FILE')
WHERE type IS NOT NULL;
"


# -------------------------------------------------------------------
# 4. INTERPRÉTATION DU SCHÉMA PAR DUCKDB
# -------------------------------------------------------------------

section "4 - TYPES INTERPRÉTÉS PAR DUCKDB"

duckdb_query "
DESCRIBE
SELECT *
FROM read_parquet('$FILE');
"


# -------------------------------------------------------------------
# 5. EXEMPLES DE DONNÉES
# -------------------------------------------------------------------

section "5 - EXEMPLES DE LIGNES"

duckdb_query "
SELECT *
FROM read_parquet('$FILE')
LIMIT 5;
"


# -------------------------------------------------------------------
# 6. STATISTIQUES PAR COLONNE
#
# Très utile pour :
# - NULL
# - minimum / maximum
# - valeurs distinctes approximatives
# - valeurs aberrantes éventuelles
# -------------------------------------------------------------------

section "6 - STATISTIQUES PAR COLONNE"

duckdb_query "
SUMMARIZE
SELECT *
FROM read_parquet('$FILE');
"


# -------------------------------------------------------------------
# 7. AUDIT DES DATES
# -------------------------------------------------------------------

section "7 - AUDIT DES DATES"

duckdb_query "
SELECT
    MIN(tpep_pickup_datetime) AS min_pickup,
    MAX(tpep_pickup_datetime) AS max_pickup,
    MIN(tpep_dropoff_datetime) AS min_dropoff,
    MAX(tpep_dropoff_datetime) AS max_dropoff,

    COUNT(*) FILTER (
        WHERE tpep_pickup_datetime < TIMESTAMP '2025-01-01'
           OR tpep_pickup_datetime >= TIMESTAMP '2025-02-01'
    ) AS pickup_outside_january

FROM read_parquet('$FILE');
"


# -------------------------------------------------------------------
# 8. AUDIT DES VALEURS ÉTONNANTES
# -------------------------------------------------------------------

section "8 - VALEURS POTENTIELLEMENT ANORMALES"

duckdb_query "
SELECT
    COUNT(*) FILTER (
        WHERE trip_distance IS NULL
    ) AS distance_null,

    COUNT(*) FILTER (
        WHERE trip_distance = 0
    ) AS distance_zero,

    COUNT(*) FILTER (
        WHERE trip_distance < 0
    ) AS distance_negative,

    COUNT(*) FILTER (
        WHERE fare_amount < 0
    ) AS fare_negative,

    COUNT(*) FILTER (
        WHERE total_amount < 0
    ) AS total_negative,

    COUNT(*) FILTER (
        WHERE passenger_count IS NULL
    ) AS passenger_count_null,

    COUNT(*) FILTER (
        WHERE tpep_dropoff_datetime < tpep_pickup_datetime
    ) AS dropoff_before_pickup

FROM read_parquet('$FILE');
"


# -------------------------------------------------------------------
# 9. CODES OBSERVÉS
#
# La signification devra ensuite être récupérée dans
# le dictionnaire officiel TLC.
# -------------------------------------------------------------------

section "9 - CODES OBSERVÉS"

duckdb_query "
SELECT
    'VendorID' AS column_name,
    CAST(VendorID AS VARCHAR) AS value,
    COUNT(*) AS row_count
FROM read_parquet('$FILE')
GROUP BY VendorID

UNION ALL

SELECT
    'RatecodeID',
    CAST(RatecodeID AS VARCHAR),
    COUNT(*)
FROM read_parquet('$FILE')
GROUP BY RatecodeID

UNION ALL

SELECT
    'payment_type',
    CAST(payment_type AS VARCHAR),
    COUNT(*)
FROM read_parquet('$FILE')
GROUP BY payment_type

UNION ALL

SELECT
    'store_and_fwd_flag',
    CAST(store_and_fwd_flag AS VARCHAR),
    COUNT(*)
FROM read_parquet('$FILE')
GROUP BY store_and_fwd_flag

ORDER BY column_name, value;
"


# -------------------------------------------------------------------
# FIN
# -------------------------------------------------------------------

section "AUDIT TERMINÉ"

echo "Reste à compléter manuellement dans la fiche source :"
echo "- signification métier de chaque colonne"
echo "- signification des codes depuis le dictionnaire TLC"
echo "- délai réel de publication"
echo "- 2 ou 3 observations intéressantes à partir des résultats ci-dessus"
