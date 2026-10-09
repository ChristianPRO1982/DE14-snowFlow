# Compte rendu — Jour 5

# Contrôler, documenter et finaliser

## État d'avancement

```text
Bloc 1 — Réponse métier finale                         ✅ TERMINÉ
Bloc 2 — Contrôle des données anormales                ✅ TERMINÉ
Bloc 3 — Consommation Snowflake                        ✅ TERMINÉ
Bloc 4 — Sécurité et droits                            ✅ TERMINÉ
Bloc 5 — Finalisation du dépôt et des livrables        ✅ TERMINÉ
Bloc 6 — Préparation de la démonstration finale        ➖ NON RÉALISÉ
```

> Aucune présentation orale n'étant prévue, le Bloc 6 n'a pas été réalisé.
> Les preuves techniques demandées pour la démonstration ont néanmoins été
> conservées dans `docs/screenshots/`.

---

# Objectif du Jour 5

Le Jour 5 consiste à valider le pipeline construit pendant les quatre premiers jours, à produire la réponse métier attendue, à contrôler la qualité des données, à mesurer la consommation Snowflake, à vérifier les droits du rôle technique et à finaliser les livrables.

Objectifs réalisés :

```text
- répondre à la question métier à partir des MARTS ;
- comparer les anomalies détectées avec MART_DATA_QUALITY ;
- mesurer la consommation de crédits Snowflake ;
- vérifier les droits du rôle TRANSFORMER ;
- vérifier qu'un accès hors périmètre est refusé ;
- finaliser le README, les documents et les captures ;
- confirmer la reproductibilité et l'idempotence du pipeline.
```

---

# Bloc 1 — Réponse métier finale ✅

## 1. Question métier

La question posée par la direction d'Hudson Cab Partners est :

> Où et quand la demande de taxis jaunes est-elle la plus forte à New York,
> et combien rapporte un trajet selon la zone, l'heure et le mode de paiement ?

Le résultat final est détaillé dans :

```text
docs/REPONSE.md
```

L'analyse repose sur janvier, février et mars 2025 après application des règles de qualité.

Volume final exploité :

```text
10 382 378 trajets valides
```

## 2. Demande par zone et heure

Table utilisée :

```text
NYC_TAXI.MARTS.MART_ZONE_HOURLY_DEMAND
```

Requête :

```sql
SELECT
    pickup_zone_name,
    pickup_borough,
    pickup_hour,
    CASE
        WHEN is_weekend THEN 'Weekend'
        ELSE 'Weekday'
    END AS day_type,
    nb_trips,
    avg_trips_per_day,
    avg_revenue_per_trip,
    revenue_per_hour_driven
FROM NYC_TAXI.MARTS.MART_ZONE_HOURLY_DEMAND
WHERE pickup_zone_name IS NOT NULL
ORDER BY avg_trips_per_day DESC
LIMIT 10;
```

Le tri est effectué sur `avg_trips_per_day` plutôt que sur `nb_trips` afin de comparer correctement semaine et week-end.

## 3. Top 10 zones × heures

| Zone | Borough | Heure | Type | Trajets | Moyenne/jour | Revenu moyen/trajet | Revenu/heure conduite |
|---|---|---:|---|---:|---:|---:|---:|
| East Village | Manhattan | 0 | Weekend | 19 187 | 738.0 | $22.84 | $113.75 |
| East Village | Manhattan | 1 | Weekend | 18 869 | 725.7 | $22.11 | $109.36 |
| Midtown Center | Manhattan | 18 | Weekday | 38 170 | 596.4 | $24.98 | $106.77 |
| Midtown Center | Manhattan | 17 | Weekday | 36 602 | 571.9 | $30.06 | $115.24 |
| West Village | Manhattan | 0 | Weekend | 14 536 | 559.1 | $23.14 | $108.21 |
| Midtown Center | Manhattan | 20 | Weekday | 34 207 | 534.5 | $22.81 | $107.93 |
| West Village | Manhattan | 1 | Weekend | 13 505 | 519.4 | $22.57 | $105.77 |
| East Village | Manhattan | 2 | Weekend | 12 976 | 519.0 | $22.00 | $117.25 |
| Midtown Center | Manhattan | 19 | Weekday | 32 773 | 512.1 | $24.14 | $113.12 |
| Midtown Center | Manhattan | 21 | Weekday | 31 636 | 494.3 | $23.01 | $108.84 |

Deux tendances principales apparaissent :

```text
Week-end, nuit
→ East Village / West Village

Semaine, fin de journée
→ Midtown Center
```

Pic observé :

```text
East Village
Weekend
00:00
738,0 trajets par jour en moyenne
```

## 4. Revenu par mode de paiement

Table utilisée :

```text
NYC_TAXI.MARTS.MART_DAILY_REVENUE
```

Requête :

```sql
SELECT
    payment_type_label,
    SUM(nb_trips) AS nb_trips,
    ROUND(SUM(total_revenue), 2) AS total_revenue,
    ROUND(
        SUM(total_revenue) / NULLIF(SUM(nb_trips), 0),
        2
    ) AS avg_revenue_per_trip
FROM NYC_TAXI.MARTS.MART_DAILY_REVENUE
GROUP BY payment_type_label
ORDER BY nb_trips DESC;
```

| Mode de paiement | Trajets | Revenu total | Revenu moyen/trajet |
|---|---:|---:|---:|
| Credit card | 7 397 954 | $209 535 888.79 | $28.32 |
| Flex Fare trip | 1 767 528 | $43 034 783.81 | $24.35 |
| Cash | 1 063 448 | $25 208 170.14 | $23.70 |
| Dispute | 115 468 | $4 065 063.99 | $35.21 |
| No charge | 37 980 | $1 038 569.87 | $27.35 |

## 5. Conclusions métier

1. La demande la plus forte se situe dans l'East Village les nuits de week-end : 738 prises en charge par jour en moyenne à minuit, puis 725,7 à 1 h.
2. En semaine, Midtown Center constitue l'autre principal point de forte demande, surtout entre 17 h et 21 h ; le pic est atteint à 18 h avec 596,4 trajets par jour en moyenne.
3. La carte bancaire est de très loin le principal mode de paiement avec près de 7,4 millions de trajets et un revenu moyen de 28,32 dollars par trajet, contre 23,70 dollars pour les espèces.

## 6. Limites

L'analyse porte uniquement sur janvier à mars 2025 et ne permet donc pas de conclure à une saisonnalité annuelle.

Les catégories `Dispute` et `No charge` sont conservées mais ne doivent pas être assimilées à des moyens de paiement commerciaux comparables à `Credit card` ou `Cash`.

### Bilan Bloc 1

```text
requête métier zone × heure                         ✅
top 10 demandé                                      ✅
analyse du revenu par mode de paiement              ✅
trois conclusions métier                            ✅
limites documentées                                 ✅
docs/REPONSE.md finalisé                            ✅
```

---

# Bloc 2 — Contrôle des données anormales ✅

## 1. Objectif

Le brief demande de compter les trajets anormaux et de comparer ces résultats avec :

```text
NYC_TAXI.MARTS.MART_DATA_QUALITY
```

Source de référence :

```text
NYC_TAXI.INTERMEDIATE.INT_TRIPS__FLAGGED
```

## 2. Requête de comparaison

```sql
WITH flagged AS (
    SELECT
        source_file_month,
        COALESCE(rejection_reason, 'valid') AS status,
        COUNT(*) AS direct_rows
    FROM NYC_TAXI.INTERMEDIATE.INT_TRIPS__FLAGGED
    GROUP BY
        source_file_month,
        COALESCE(rejection_reason, 'valid')
),
quality AS (
    SELECT
        source_file_month,
        status,
        nb_rows AS mart_rows,
        pct_of_file
    FROM NYC_TAXI.MARTS.MART_DATA_QUALITY
)
SELECT
    COALESCE(f.source_file_month, q.source_file_month) AS source_file_month,
    COALESCE(f.status, q.status) AS rejection_reason,
    f.direct_rows,
    q.mart_rows,
    COALESCE(f.direct_rows, 0) - COALESCE(q.mart_rows, 0) AS difference,
    q.pct_of_file,
    CASE
        WHEN f.direct_rows = q.mart_rows THEN 'OK'
        ELSE 'DIFFERENCE'
    END AS comparison
FROM flagged f
FULL OUTER JOIN quality q
    ON q.source_file_month = f.source_file_month
   AND q.status = f.status
WHERE COALESCE(f.status, q.status) <> 'valid'
ORDER BY
    source_file_month,
    rejection_reason;
```

## 3. Résultats

| Mois | Motif | Direct | Mart | Différence | % fichier | Comparaison |
|---|---|---:|---:|---:|---:|---|
| 2025-01-01 | amount_non_positive | 130 112 | 130 112 | 0 | 3.744 | OK |
| 2025-01-01 | distance_out_of_range | 90 327 | 90 327 | 0 | 2.599 | OK |
| 2025-01-01 | duration_non_positive | 2 051 | 2 051 | 0 | 0.059 | OK |
| 2025-01-01 | duration_too_long | 1 377 | 1 377 | 0 | 0.040 | OK |
| 2025-01-01 | pickup_outside_file_month | 22 | 22 | 0 | 0.001 | OK |
| 2025-02-01 | amount_non_positive | 166 569 | 166 569 | 0 | 4.656 | OK |
| 2025-02-01 | distance_out_of_range | 99 232 | 99 232 | 0 | 2.774 | OK |
| 2025-02-01 | duration_non_positive | 5 164 | 5 164 | 0 | 0.144 | OK |
| 2025-02-01 | duration_too_long | 1 301 | 1 301 | 0 | 0.036 | OK |
| 2025-02-01 | pickup_outside_file_month | 31 | 31 | 0 | 0.001 | OK |
| 2025-03-01 | amount_non_positive | 192 454 | 192 454 | 0 | 4.643 | OK |
| 2025-03-01 | distance_out_of_range | 103 121 | 103 121 | 0 | 2.488 | OK |
| 2025-03-01 | duration_non_positive | 22 280 | 22 280 | 0 | 0.538 | OK |
| 2025-03-01 | duration_too_long | 1 574 | 1 574 | 0 | 0.038 | OK |
| 2025-03-01 | pickup_outside_file_month | 33 | 33 | 0 | 0.001 | OK |

Pour chaque mois et chaque motif :

```text
DIRECT_ROWS = MART_ROWS
DIFFERENCE  = 0
COMPARISON  = OK
```

## 4. Taux de rejet

```text
Janvier 2025  ≈ 6,443 %
Février 2025  ≈ 7,611 %
Mars 2025     ≈ 7,708 %
```

Tous restent sous :

```text
max_rejection_pct = 10
```

## 5. Contrôles Airflow

Trois contrôles SQL sont intégrés au DAG :

```text
check_raw_month_loaded
intermediate.check_rejection_rate
marts.check_trips_no_duplicates
```

Deux contrôles propres au projet ont été ajoutés :

```text
intermediate.check_rejection_rate
marts.check_trips_no_duplicates
```

Un échec volontaire a été testé avec :

```text
max_rejection_pct = 0
```

Le contrôle a retourné `False` et la tâche Airflow a échoué comme attendu.

Preuve :

```text
docs/screenshots/03_airflow_failed_quality_control.png
```

### Bilan Bloc 2

```text
anomalies comptées                                    ✅
comparaison avec MART_DATA_QUALITY                    ✅
aucune différence détectée                            ✅
taux de rejet < 10 %                                  ✅
deux contrôles SQL supplémentaires                    ✅
échec volontaire d'un contrôle testé                  ✅
```

---

# Bloc 3 — Consommation Snowflake ✅

## 1. Warehouse

```text
Nom                : NYC_TAXI_WH
Type               : STANDARD
Taille             : X-Small
État               : SUSPENDED
Min clusters       : 1
Max clusters       : 1
Auto-suspend       : 60 secondes
Auto-resume        : true
Owner              : SYSADMIN
Resource constraint: STANDARD_GEN_2
```

Le brief demandait un warehouse X-Small avec auto-suspend inférieur ou égal à 60 secondes : la configuration est conforme.

## 2. Mesure des crédits

```sql
SELECT
    warehouse_name,
    ROUND(SUM(credits_used), 4) AS credits_used,
    ROUND(SUM(credits_used_compute), 4) AS compute_credits,
    ROUND(SUM(credits_used_cloud_services), 4) AS cloud_services_credits
FROM TABLE(
    INFORMATION_SCHEMA.WAREHOUSE_METERING_HISTORY(
        DATE_RANGE_START => DATEADD('day', -30, CURRENT_DATE()),
        DATE_RANGE_END => CURRENT_DATE(),
        WAREHOUSE_NAME => 'NYC_TAXI_WH'
    )
)
GROUP BY warehouse_name;
```

Dernière mesure réalisée :

```text
Crédits totaux : 0,8312
Compute        : 0,8130
Cloud services : 0,0182
```

Preuve :

```text
docs/screenshots/06_snowflake_credits.png
```

### Bilan Bloc 3

```text
warehouse X-Small                                   ✅
auto-suspend 60 secondes                            ✅
auto-resume activé                                  ✅
crédits mesurés                                     ✅
capture conservée                                   ✅
```

---

# Bloc 4 — Sécurité et droits ✅

## 1. Rôle technique

Utilisateur de service :

```text
AIRFLOW_SVC
```

Rôle :

```text
TRANSFORMER
```

Le rôle suit le principe du moindre privilège.

## 2. Principaux droits

```text
USAGE sur NYC_TAXI

USAGE sur :
- RAW
- STAGING
- INTERMEDIATE
- MARTS

RAW :
- CREATE FILE FORMAT
- CREATE STAGE
- CREATE TABLE

STAGING :
- CREATE TABLE
- CREATE VIEW

INTERMEDIATE :
- CREATE TABLE
- CREATE VIEW

MARTS :
- CREATE TABLE
- CREATE VIEW

NYC_TAXI_WH :
- USAGE
- OPERATE
```

Preuve :

```text
docs/screenshots/05_snowflake_transformer_grants.png
```

## 3. Test dans le périmètre

```sql
SELECT COUNT(*) AS nb_trips
FROM NYC_TAXI.MARTS.FCT_TRIPS;
```

Résultat :

```text
10 382 378
```

## 4. Test hors périmètre

```sql
CREATE DATABASE SHOULD_FAIL;
```

Résultat :

```text
SQL access control error:
Insufficient privileges to operate on account.
Your primary role TRANSFORMER must have CREATE DATABASE granted on ACCOUNT.
```

Le rôle peut donc exécuter le pipeline sans disposer de droits administratifs au niveau du compte.

## 5. Authentification

Airflow se connecte avec `AIRFLOW_SVC` via paire de clés RSA.

La clé privée n'est pas versionnée.

### Bilan Bloc 4

```text
utilisateur de service dédié                         ✅
rôle TRANSFORMER dédié                               ✅
least privilege                                      ✅
authentification RSA                                 ✅
clé privée non versionnée                            ✅
lecture dans le périmètre                            ✅
CREATE DATABASE refusé hors périmètre                ✅
```

---

# Bloc 5 — Finalisation du dépôt et des livrables ✅

## 1. Correction de reproductibilité Parquet

Un problème important a été identifié : le format Parquet Snowflake utilisait initialement :

```text
USE_LOGICAL_TYPE = FALSE
```

Les timestamps logiques Parquet étaient mal interprétés, produisant des durées environ un million de fois trop grandes.

Correction persistée :

```sql
CREATE OR REPLACE FILE FORMAT PARQUET_FF
  TYPE = PARQUET
  USE_LOGICAL_TYPE = TRUE;
```

Fichier :

```text
snowflake/02_raw.sql
```

## 2. Idempotence

Replay de février 2025 :

```text
INT_TRIPS__FLAGGED : 3 577 543
INT_TRIPS__ENRICHED: 3 305 246
FCT_TRIPS          : 3 305 246
```

Les volumes sont identiques avant et après replay.

Le contrôle :

```text
marts.check_trips_no_duplicates
```

vérifie aussi :

```text
COUNT(*) = COUNT(DISTINCT trip_sk)
```

## 3. Volumes finaux

RAW :

```text
Janvier 2025 : 3 475 226
Février 2025 : 3 577 543
Mars 2025    : 4 145 257
Total RAW    : 11 198 026
```

FCT_TRIPS :

```text
Janvier 2025 : 3 251 337
Février 2025 : 3 305 246
Mars 2025    : 3 825 795
Total FCT    : 10 382 378
```

## 4. Sécurité du dépôt

Le `.gitignore` racine protège notamment :

```text
.env
*.p8
__pycache__/
*.py[cod]
.venv/
parquet/*.parquet
csv/*.csv
```

La vérification suivante n'a retourné aucun fichier sensible ou donnée source suivie :

```bash
git ls-files | grep -E '(^|/)\.env$|\.p8$|\.pem$|\.key$|^parquet/.*\.parquet$|^csv/.*\.csv$' || true
```

## 5. Historique de chargement

Les chargements de janvier, février et mars apparaissent avec le statut :

```text
Loaded
```

Preuve :

```text
docs/screenshots/04_snowflake_load_history.png
```

## 6. Captures

```text
docs/screenshots/01_airflow_three_successful_runs.png
docs/screenshots/02_airflow_dag_graph.png
docs/screenshots/03_airflow_failed_quality_control.png
docs/screenshots/04_snowflake_load_history.png
docs/screenshots/05_snowflake_transformer_grants.png
docs/screenshots/06_snowflake_credits.png
```

Elles couvrent les preuves demandées : trois runs Airflow, graphe du DAG, quality gate en échec, load history, droits et crédits.

## 7. Livrables principaux

```text
README.md
snowflake/01_infrastructure.sql
snowflake/02_raw.sql
ingestion/
airflow/
docs/fiche_trajets.md
docs/REPONSE.md
docs/screenshots/
rendu/jour1.md
rendu/jour2.md
rendu/jour3.md
rendu/jour4.md
rendu/jour5.md
.gitignore
```

### Bilan Bloc 5

```text
README finalisé                                      ✅
REPONSE.md finalisé                                  ✅
qualité contrôlée                                    ✅
crédits mesurés                                      ✅
droits vérifiés                                      ✅
accès hors périmètre refusé                          ✅
reproductibilité PARQUET_FF corrigée                 ✅
idempotence vérifiée                                 ✅
secrets absents de l'index Git                       ✅
données téléchargées absentes de l'index Git         ✅
fiche source présente                                ✅
6 captures de validation présentes                   ✅
```

---

# Bloc 6 — Présentation orale ➖

Aucune présentation orale n'étant prévue, aucune préparation spécifique de soutenance n'a été réalisée.

Les preuves qui auraient permis de faire cette démonstration restent toutefois disponibles :

```text
- droits du rôle TRANSFORMER ;
- refus d'accès hors périmètre ;
- trois exécutions Airflow réussies ;
- graphe du DAG ;
- replay idempotent de février 2025 ;
- échec volontaire du quality gate ;
- requête métier finale ;
- mesure des crédits Snowflake.
```

---

# Bilan final du Jour 5 ✅

```text
Réponse métier finale                               ✅
10 382 378 trajets valides analysés                 ✅
Anomalies comparées à MART_DATA_QUALITY             ✅
Taux de rejet < 10 % sur les trois mois             ✅
Deux quality gates SQL supplémentaires              ✅
Replay idempotent vérifié                           ✅
Warehouse X-Small avec auto-suspend 60 s            ✅
Crédits Snowflake mesurés                           ✅
Rôle TRANSFORMER limité au périmètre utile          ✅
Accès administratif hors périmètre refusé           ✅
Authentification RSA                                ✅
Secrets non versionnés                              ✅
Correction USE_LOGICAL_TYPE persistée               ✅
README finalisé                                     ✅
REPONSE.md finalisé                                 ✅
Captures de validation conservées                   ✅
```

Le pipeline est reproductible, idempotent, contrôlé et documenté.

La préparation d'une soutenance n'a pas été réalisée car aucune présentation orale n'est prévue.
