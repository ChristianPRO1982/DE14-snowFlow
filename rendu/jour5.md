# Compte rendu — Jour 5

# Contrôler, documenter et présenter

## État d'avancement

```text
Bloc 1 — Réponse métier finale                         ✅ TERMINÉ
Bloc 2 — Contrôle des données anormales                ✅ TERMINÉ
Bloc 3 — Consommation Snowflake                        ✅ TERMINÉ
Bloc 4 — Sécurité et droits                            ✅ TERMINÉ
Bloc 5 — Finalisation du dépôt et des livrables        ✅ TERMINÉ
Bloc 6 — Préparation de la démonstration finale        ⏳ À FAIRE
```

---

# Objectif du Jour 5

Le Jour 5 consiste à valider le pipeline construit pendant les quatre premiers jours, à produire la réponse métier attendue par la direction, à vérifier la qualité des données et la maîtrise de l'entrepôt Snowflake, puis à finaliser les livrables et préparer la démonstration.

Les objectifs sont :

```text
- répondre à la question métier à partir des MARTS ;
- comparer les anomalies détectées avec MART_DATA_QUALITY ;
- mesurer la consommation de crédits Snowflake ;
- vérifier les droits du rôle des outils ;
- finaliser le README, les captures et les documents ;
- préparer une démonstration technique reproductible.
```

---

# Bloc 1 — Réponse métier finale ✅

## 1. Question métier

La question posée par la direction d'Hudson Cab Partners est :

> Où et quand la demande de taxis jaunes est-elle la plus forte à New York,
> et combien rapporte un trajet selon la zone, l'heure et le mode de paiement ?

Le résultat final est documenté dans :

```text
docs/REPONSE.md
```

L'analyse repose sur les données de janvier, février et mars 2025, après application des règles de qualité du pipeline.

Volume final exploité :

```text
10 382 378 trajets valides
```

---

## 2. Analyse de la demande par zone et heure

La table utilisée est :

```text
NYC_TAXI.MARTS.MART_ZONE_HOURLY_DEMAND
```

Elle permet d'analyser la demande selon :

```text
zone de prise en charge
× heure
× type de jour
```

La requête finale est :

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

Le tri utilise :

```text
avg_trips_per_day
```

plutôt que le nombre total brut de trajets, afin de comparer correctement les jours de semaine et les week-ends, qui ne sont pas présents en nombre égal sur la période.

---

## 3. Top 10 zones × heures

| Zone | Borough | Heure | Type de jour | Trajets | Moyenne trajets/jour | Revenu moyen/trajet |
|---|---|---:|---|---:|---:|---:|
| East Village | Manhattan | 0 | Weekend | 19 187 | 738.0 | $22.84 |
| East Village | Manhattan | 1 | Weekend | 18 869 | 725.7 | $22.11 |
| Midtown Center | Manhattan | 18 | Weekday | 38 170 | 596.4 | $24.98 |
| Midtown Center | Manhattan | 17 | Weekday | 36 602 | 571.9 | $30.06 |
| West Village | Manhattan | 0 | Weekend | 14 536 | 559.1 | $23.14 |
| Midtown Center | Manhattan | 20 | Weekday | 34 207 | 534.5 | $22.81 |
| West Village | Manhattan | 1 | Weekend | 13 505 | 519.4 | $22.57 |
| East Village | Manhattan | 2 | Weekend | 12 976 | 519.0 | $22.00 |
| Midtown Center | Manhattan | 19 | Weekday | 32 773 | 512.1 | $24.14 |
| Midtown Center | Manhattan | 21 | Weekday | 31 636 | 494.3 | $23.01 |

Deux comportements principaux apparaissent :

```text
week-end, nuit
→ East Village / West Village

semaine, fin de journée
→ Midtown Center
```

Le maximum observé est :

```text
East Village
Weekend
00:00
738,0 trajets par jour en moyenne
```

---

## 4. Analyse du revenu selon le mode de paiement

La table utilisée est :

```text
NYC_TAXI.MARTS.MART_DAILY_REVENUE
```

La requête finale est :

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

Résultat :

| Mode de paiement | Trajets | Revenu total | Revenu moyen/trajet |
|---|---:|---:|---:|
| Credit card | 7 397 954 | $209 535 888.79 | $28.32 |
| Flex Fare trip | 1 767 528 | $43 034 783.81 | $24.35 |
| Cash | 1 063 448 | $25 208 170.14 | $23.70 |
| Dispute | 115 468 | $4 065 063.99 | $35.21 |
| No charge | 37 980 | $1 038 569.87 | $27.35 |

La carte bancaire représente de très loin le principal moyen de paiement observé.

---

## 5. Conclusions métier

Les trois conclusions intégrées dans `docs/REPONSE.md` sont :

1. La demande la plus forte se situe dans l'East Village les nuits de week-end : à minuit, on observe en moyenne 738 prises en charge par jour, puis 725,7 à 1 h.

2. En semaine, Midtown Center constitue l'autre principal point de forte demande, surtout entre 17 h et 21 h ; le pic est atteint à 18 h avec 596,4 trajets par jour en moyenne.

3. La carte bancaire est de très loin le principal mode de paiement avec près de 7,4 millions de trajets et un revenu moyen de 28,32 dollars par trajet, contre 23,70 dollars pour les paiements en espèces.

---

## 6. Limites de l'analyse

L'analyse porte uniquement sur :

```text
janvier 2025
février 2025
mars 2025
```

Elle utilise uniquement les trajets ayant passé les règles de qualité du pipeline.

Les résultats ne permettent donc pas à eux seuls de conclure à une saisonnalité annuelle.

Les catégories :

```text
Dispute
No charge
```

sont conservées dans les données mais ne doivent pas être interprétées comme des moyens de paiement commerciaux comparables à la carte bancaire ou aux espèces.

---

# Bilan du Bloc 1 ✅

```text
requête métier zone × heure                         ✅
top 10 demandé                                      ✅
analyse du revenu par mode de paiement              ✅
trois conclusions pour la direction                 ✅
limites documentées                                 ✅
docs/REPONSE.md créé                                 ✅
```

Le Bloc 1 du Jour 5 est terminé.

---

# Bloc 2 — Contrôle des données anormales ✅

## 1. Objectif

Le brief demande de compter les trajets anormaux et de comparer ces résultats avec :

```text
NYC_TAXI.MARTS.MART_DATA_QUALITY
```

La source de référence utilisée pour le contrôle est :

```text
NYC_TAXI.INTERMEDIATE.INT_TRIPS__FLAGGED
```

Chaque trajet rejeté possède une valeur dans :

```text
rejection_reason
```

Le but est de vérifier que les agrégats publiés dans `MART_DATA_QUALITY` correspondent exactement aux anomalies détectées dans la couche `INTERMEDIATE`.

---

## 2. Requête de comparaison

La requête utilisée est :

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

Cette requête compare directement :

```text
nombre d'anomalies dans INT_TRIPS__FLAGGED
=
nombre d'anomalies publié dans MART_DATA_QUALITY
```

---

## 3. Résultats

| Mois | Motif de rejet | INT_TRIPS__FLAGGED | MART_DATA_QUALITY | Différence | % fichier | Comparaison |
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

Le mart de qualité reflète donc exactement les anomalies présentes dans `INT_TRIPS__FLAGGED`.

---

## 4. Taux global de rejet

Les taux globaux de rejet observés sont d'environ :

```text
Janvier 2025  ≈ 6,443 %
Février 2025  ≈ 7,611 %
Mars 2025     ≈ 7,708 %
```

Ils restent donc tous inférieurs au seuil défini dans le DAG :

```text
max_rejection_pct = 10
```

Ce résultat est cohérent avec le succès du contrôle Airflow :

```text
intermediate.check_rejection_rate
```

sur les trois exécutions finales.

---

## 5. Principaux motifs de rejet

Les deux principales causes de rejet sur les trois mois sont :

```text
amount_non_positive
distance_out_of_range
```

Le motif `duration_non_positive` est beaucoup moins fréquent, mais augmente nettement en mars.

Les motifs :

```text
duration_too_long
pickup_outside_file_month
```

restent très minoritaires.

---

## 6. Cohérence avec la réponse métier

`docs/REPONSE.md` indique que l'analyse métier porte uniquement sur les trajets ayant passé les règles de qualité.

Le contrôle réalisé ici confirme que les anomalies ont bien été identifiées et agrégées de manière cohérente avant l'exploitation des données dans les marts analytiques.

Une mention synthétique peut être conservée dans la section `Limites` de `docs/REPONSE.md` :

```text
La qualité des données a été contrôlée avant l'analyse.
Les anomalies détectées dans INT_TRIPS__FLAGGED correspondent exactement
aux agrégats publiés dans MART_DATA_QUALITY.

Les principaux motifs de rejet sont les montants non positifs et les
distances hors plage autorisée. Le taux global de rejet reste inférieur
au seuil de 10 % pour chacun des trois mois étudiés.
```

---

# Bilan du Bloc 2 ✅

```text
anomalies comptées dans INT_TRIPS__FLAGGED             ✅
comparaison avec MART_DATA_QUALITY                      ✅
aucune différence détectée                              ✅
principaux motifs de rejet identifiés                   ✅
taux de rejet mensuels < 10 %                           ✅
cohérence avec le quality gate Airflow                  ✅
```

Le Bloc 2 du Jour 5 est terminé.

---

# Bloc 3 — Consommation Snowflake ✅

## 1. Objectif

Le brief demande de mesurer les crédits consommés par le warehouse Snowflake et de vérifier que sa configuration respecte les contraintes prévues pour le projet.

Le warehouse utilisé est :

```text
NYC_TAXI_WH
```

Les points à contrôler sont :

```text
taille du warehouse
auto-suspend
état courant
auto-resume
crédits consommés
```

---

## 2. Vérification de la configuration du warehouse

La commande utilisée est :

```sql
SHOW WAREHOUSES LIKE 'NYC_TAXI_WH';
```

Résultat principal :

| Paramètre | Valeur |
|---|---|
| Name | NYC_TAXI_WH |
| State | SUSPENDED |
| Type | STANDARD |
| Size | X-Small |
| Min cluster count | 1 |
| Max cluster count | 1 |
| Auto suspend | 60 |
| Auto resume | true |
| Owner | SYSADMIN |

La configuration respecte donc les contraintes du brief :

```text
warehouse unique
taille X-Small
AUTO_SUSPEND = 60 secondes
AUTO_RESUME = true
```

L'état courant :

```text
SUSPENDED
```

confirme également que le warehouse s'arrête automatiquement lorsqu'il n'est plus utilisé.

---

## 3. Mesure des crédits consommés

La requête utilisée est :

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

Résultat :

| Warehouse | Crédits totaux | Compute | Cloud services |
|---|---:|---:|---:|
| NYC_TAXI_WH | 0.7612 | 0.7433 | 0.0179 |

La consommation mesurée sur la période est donc :

```text
0,7612 crédit
```

dont :

```text
0,7433 crédit de compute
0,0179 crédit de cloud services
```

En proportion, cela représente environ :

```text
97,6 % de compute
2,4 % de cloud services
```

---

## 4. Interprétation

Le warehouse est dimensionné au niveau minimal demandé pour le projet :

```text
X-Small
```

et sa suspension automatique est réglée sur :

```text
60 secondes
```

Cette configuration limite les périodes pendant lesquelles le warehouse reste actif sans exécuter de requête.

La consommation totale reste faible malgré :

```text
- le chargement de janvier, février et mars 2025 ;
- plusieurs replays Airflow ;
- les transformations STAGING, INTERMEDIATE et MARTS ;
- les contrôles de qualité ;
- le traitement final de plus de 10 millions de trajets valides.
```

La valeur à retenir pour la démonstration est :

```text
Warehouse : NYC_TAXI_WH
Taille : X-Small
Auto-suspend : 60 secondes
État observé : SUSPENDED
Crédits consommés : 0,7612
```

---

# Bilan du Bloc 3 ✅

```text
warehouse NYC_TAXI_WH vérifié                         ✅
taille X-Small                                        ✅
AUTO_SUSPEND = 60 secondes                            ✅
AUTO_RESUME activé                                    ✅
warehouse observé à l'état SUSPENDED                  ✅
crédits consommés mesurés                             ✅
consommation totale = 0,7612 crédit                   ✅
```

Le Bloc 3 du Jour 5 est terminé.

---

# Bloc 4 — Sécurité et droits ✅

## 1. Objectif

Le brief demande de vérifier que le rôle utilisé par les outils possède uniquement les droits nécessaires au pipeline, et de démontrer qu'un accès hors périmètre est refusé.

Le rôle utilisé par Airflow est :

```text
TRANSFORMER
```

L'utilisateur de service est :

```text
AIRFLOW_SVC
```

L'objectif est de démontrer les trois points suivants :

```text
- TRANSFORMER peut travailler dans NYC_TAXI ;
- AIRFLOW_SVC utilise bien TRANSFORMER ;
- TRANSFORMER ne possède pas de privilèges administratifs au niveau du compte.
```

---

## 2. Vérification des privilèges du rôle TRANSFORMER

La commande utilisée est :

```sql
SHOW GRANTS TO ROLE TRANSFORMER;
```

Les privilèges principaux observés sont :

```text
DATABASE NYC_TAXI
- USAGE

WAREHOUSE NYC_TAXI_WH
- USAGE
- OPERATE

SCHEMA NYC_TAXI.RAW
- USAGE
- CREATE TABLE
- CREATE STAGE
- CREATE FILE FORMAT

SCHEMA NYC_TAXI.STAGING
- USAGE
- CREATE TABLE
- CREATE VIEW

SCHEMA NYC_TAXI.INTERMEDIATE
- USAGE
- CREATE TABLE
- CREATE VIEW

SCHEMA NYC_TAXI.MARTS
- USAGE
- CREATE TABLE
- CREATE VIEW
```

Le rôle est également propriétaire des objets qu'il a créés dans le cadre du pipeline, notamment :

```text
RAW
- PARQUET_FF
- CSV_FF
- NYC_TAXI_STAGE
- TAXI_ZONE_LOOKUP
- YELLOW_TRIPDATA

STAGING
- STG_TLC__YELLOW_TRIPS
- STG_TLC__TAXI_ZONES
- PAYMENT_TYPE_CODES
- RATE_CODE_CODES
- VENDOR_CODES

INTERMEDIATE
- INT_TRIPS__FLAGGED
- INT_TRIPS__ENRICHED

MARTS
- FCT_TRIPS
- DIM_DATE
- DIM_PAYMENT_TYPE
- DIM_RATE_CODE
- DIM_VENDOR
- DIM_ZONE
- MART_DAILY_REVENUE
- MART_DATA_QUALITY
- MART_ZONE_HOURLY_DEMAND
```

Ces droits sont cohérents avec les besoins du pipeline : le rôle peut créer et manipuler les objets de la base `NYC_TAXI`, utiliser le warehouse dédié, mais ne dispose pas de privilèges administratifs globaux sur le compte.

---

## 3. Vérification de l'utilisateur AIRFLOW_SVC

La commande utilisée est :

```sql
SHOW GRANTS TO USER AIRFLOW_SVC;
```

Résultat :

| Privilège | Objet | Rôle | Utilisateur |
|---|---|---|---|
| USAGE | ROLE | TRANSFORMER | AIRFLOW_SVC |

L'utilisateur de service utilise donc bien :

```text
TRANSFORMER
```

et aucun rôle administratif supplémentaire n'est nécessaire pour exécuter le pipeline.

---

## 4. Preuve d'un accès autorisé

Le test suivant a été exécuté avec le rôle :

```text
TRANSFORMER
```

Requête :

```sql
SELECT COUNT(*) AS nb_trips
FROM NYC_TAXI.MARTS.FCT_TRIPS;
```

Résultat :

```text
NB_TRIPS = 10 382 378
```

Le rôle peut donc bien accéder aux données produites par le pipeline dans son périmètre fonctionnel.

---

## 5. Preuve d'un accès refusé hors périmètre

Le test suivant a ensuite été exécuté avec le même rôle :

```sql
CREATE DATABASE SHOULD_FAIL;
```

Résultat :

```text
SQL access control error:
Insufficient privileges to operate on account 'ZN63987'.
Your primary role TRANSFORMER must have CREATE DATABASE granted
on ACCOUNT ZN63987.
```

L'échec est attendu.

Il démontre que :

```text
TRANSFORMER
```

ne possède pas le privilège :

```text
CREATE DATABASE
```

au niveau du compte Snowflake.

---

## 6. Interprétation

Le rôle `TRANSFORMER` respecte le principe de moindre privilège appliqué au périmètre du projet :

```text
il peut utiliser NYC_TAXI_WH ;
il peut créer et manipuler les objets nécessaires dans NYC_TAXI ;
il peut lire les données finales du pipeline ;
il ne peut pas créer une nouvelle base au niveau du compte.
```

Les nombreux privilèges `OWNERSHIP` visibles sur les tables, vues, stages et file formats sont normaux : ces objets ont été créés par le rôle `TRANSFORMER`, qui en devient donc propriétaire.

Cela ne lui donne pas pour autant des droits administratifs globaux sur le compte Snowflake.

La formulation à retenir pour la soutenance est :

> Le rôle `TRANSFORMER` peut créer et manipuler les objets nécessaires au pipeline dans `NYC_TAXI` et utiliser le warehouse dédié, mais il ne possède pas de privilèges administratifs au niveau du compte. L'utilisateur de service `AIRFLOW_SVC` utilise uniquement ce rôle.

---

# Bilan du Bloc 4 ✅

```text
droits de TRANSFORMER vérifiés                         ✅
AIRFLOW_SVC utilise TRANSFORMER                        ✅
accès à NYC_TAXI.MARTS validé                         ✅
10 382 378 trajets accessibles                         ✅
accès hors périmètre testé                             ✅
CREATE DATABASE refusé                                 ✅
principe de moindre privilège démontré                 ✅
```

Le Bloc 4 du Jour 5 est terminé.

---

# Suite du Jour 5

```text
Bloc 5 — Finalisation du dépôt et des livrables
Bloc 6 — Préparation de la démonstration finale
```
