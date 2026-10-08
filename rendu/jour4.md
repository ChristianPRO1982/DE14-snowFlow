# Compte rendu — Jour 4

# Transformer et contrôler les données avec Airflow

## État d'avancement

```text
Bloc 1 — Lire et comprendre les fichiers SQL fournis           ✅ TERMINÉ
Bloc 2 — Ajouter les transformations SQL au DAG                ✅ TERMINÉ
Bloc 3 — Ajouter les contrôles de qualité                       ✅ TERMINÉ
Bloc 4 — Provoquer volontairement l'échec d'un contrôle        ✅ TERMINÉ
Bloc 5 — Rejouer février et vérifier l'idempotence              ✅ TERMINÉ
Bloc 6 — Validation finale du Jour 4                            ✅ TERMINÉ
```

---

# Objectif du Jour 4

Le Jour 3 a permis d'automatiser le chargement mensuel des fichiers Yellow Taxi dans la couche `RAW`.

Le Jour 4 doit compléter le pipeline :

```text
RAW
 ↓
STAGING
 ↓
INTERMEDIATE
 ↓
MARTS
 ↓
CONTROLES
```

Airflow doit orchestrer les fichiers SQL fournis dans le bon ordre et pour le bon mois.

Les objectifs du brief sont :

```text
- lire et comprendre les SQL fournis ;
- en déduire les dépendances ;
- ajouter une tâche Airflow par fichier SQL ;
- regrouper les tâches par couche ;
- brancher le contrôle RAW fourni ;
- écrire au moins deux contrôles supplémentaires ;
- vérifier qu'un contrôle en échec bloque les tâches suivantes ;
- rejouer février sans créer de doublons ;
- obtenir trois exécutions réussies ;
- obtenir 10 382 378 trajets valides dans MARTS.FCT_TRIPS.
```

---

# Bloc 1 — Comprendre les fichiers SQL fournis ✅

## 1. Inventaire

Les fichiers SQL se trouvent dans :

```text
airflow/include/sql/
```

Arborescence :

```text
airflow/include/sql/
├── 00_tables.sql
├── controles/
│   └── raw_mois_charge.sql
├── intermediate/
│   ├── int_trips__enriched.sql
│   └── int_trips__flagged.sql
├── marts/
│   ├── dim_date.sql
│   ├── dim_payment_type.sql
│   ├── dim_rate_code.sql
│   ├── dim_vendor.sql
│   ├── dim_zone.sql
│   ├── fct_trips.sql
│   ├── mart_daily_revenue.sql
│   ├── mart_data_quality.sql
│   └── mart_zone_hourly_demand.sql
└── staging/
    ├── codes_tlc.sql
    ├── stg_tlc__taxi_zones.sql
    └── stg_tlc__yellow_trips.sql
```

Principe retenu :

```text
une tâche Airflow
=
un fichier SQL
```

---

## 2. `00_tables.sql`

Ce fichier crée trois tables persistantes :

```text
NYC_TAXI.INTERMEDIATE.INT_TRIPS__FLAGGED
NYC_TAXI.INTERMEDIATE.INT_TRIPS__ENRICHED
NYC_TAXI.MARTS.FCT_TRIPS
```

Il utilise :

```sql
CREATE TABLE IF NOT EXISTS
```

Ce choix rend la création idempotente.

Ces tables sont alimentées mois par mois avec le pattern :

```text
DELETE du mois
+
INSERT du mois recalculé
```

Cela permet de rejouer un mois sans dupliquer les données.

### `INT_TRIPS__FLAGGED`

Contient tous les trajets, y compris les invalides.

```text
rejection_reason IS NULL
→ trajet valide

rejection_reason IS NOT NULL
→ trajet rejeté
```

### `INT_TRIPS__ENRICHED`

Contient les trajets :

```text
valides
+
dédoublonnés
+
enrichis
```

Principales colonnes dérivées :

```text
trip_sk
pickup_date
pickup_date_key
pickup_hour
pickup_day_of_week_iso
is_weekend
trip_duration_min
avg_speed_mph
tip_rate_pct
```

### `FCT_TRIPS`

Table de faits centrale.

Grain :

```text
1 ligne = 1 trajet valide
```

Clés vers les dimensions :

```text
pickup_date_key
pickup_zone_key
dropoff_zone_key
payment_type_key
rate_code_key
vendor_key
```

---

## 3. `staging/stg_tlc__yellow_trips.sql`

Source :

```text
RAW.YELLOW_TRIPDATA
```

Destination :

```text
STAGING.STG_TLC__YELLOW_TRIPS
```

Cette vue effectue :

```text
renommage
+
typage
+
normalisation légère
```

Elle n'applique :

```text
aucun filtre
aucune jointure
```

Elle doit donc contenir exactement autant de lignes que la RAW.

Exemples :

```text
vendorid       → vendor_key
ratecodeid     → rate_code_key
payment_type   → payment_type_key
pulocationid   → pickup_zone_key
dolocationid   → dropoff_zone_key
```

Normalisation :

```sql
COALESCE(ratecodeid, 99)::integer
```

Le flag `Y/N` devient un booléen :

```sql
store_and_fwd_flag = 'Y' AS is_store_and_forward
```

### Traçabilité mensuelle

Le mois est extrait du nom du fichier :

```text
yellow_tripdata_2025-02.parquet
→ source_file_month = 2025-02-01
```

avec :

```sql
TO_DATE(
    REGEXP_SUBSTR(_source_file, '[0-9]{4}-[0-9]{2}'),
    'YYYY-MM'
)
```

Pour l'idempotence, le mois de traitement doit être basé sur :

```text
source_file_month
```

et non sur `pickup_at`.

---

## 4. `staging/stg_tlc__taxi_zones.sql`

Source :

```text
RAW.TAXI_ZONE_LOOKUP
```

Destination :

```text
STAGING.STG_TLC__TAXI_ZONES
```

Correspondances :

```text
locationid   → zone_key
zone         → zone_name
borough      → borough
service_zone → service_zone
_source_file → source_file
_loaded_at   → loaded_at
```

`zone_key` servira de clé de référence pour :

```text
pickup_zone_key
dropoff_zone_key
```

---

## 5. `staging/codes_tlc.sql`

Ce fichier crée trois petites tables de référence :

```text
STAGING.PAYMENT_TYPE_CODES
STAGING.RATE_CODE_CODES
STAGING.VENDOR_CODES
```

Exemples :

```text
payment_type_key = 1 → Credit card
rate_code_key = 2    → JFK
vendor_key = 2       → Curb Mobility, LLC
```

Elles utilisent :

```sql
CREATE OR REPLACE TABLE
```

et sont entièrement reproductibles car leur contenu est codé dans le SQL.

Elles alimenteront :

```text
DIM_PAYMENT_TYPE
DIM_RATE_CODE
DIM_VENDOR
```

---

## 6. `intermediate/int_trips__flagged.sql`

Source :

```text
STAGING.STG_TLC__YELLOW_TRIPS
```

Destination :

```text
INTERMEDIATE.INT_TRIPS__FLAGGED
```

Première vraie couche de règles métier.

### Idempotence

```sql
DELETE FROM NYC_TAXI.INTERMEDIATE.INT_TRIPS__FLAGGED
WHERE source_file_month = '{{ ds }}'::date;
```

Puis le mois est recalculé et réinséré.

### Paramétrage Airflow

Le SQL utilise :

```jinja
{{ ds }}
{{ params.max_trip_duration_min }}
{{ params.max_trip_distance_miles }}
```

Pour février 2025 :

```text
{{ ds }} → 2025-02-01
```

### Durée

```sql
DATEDIFF('second', pickup_at, dropoff_at) / 60.0
```

### Motifs de rejet

```text
timestamp_null
duration_non_positive
duration_too_long
pickup_outside_file_month
distance_out_of_range
amount_non_positive
zone_null
```

Sinon :

```text
rejection_reason = NULL
```

Les trajets rejetés sont conservés pour assurer la traçabilité et permettre les analyses de qualité.

---

## 7. `intermediate/int_trips__enriched.sql`

Source :

```text
INTERMEDIATE.INT_TRIPS__FLAGGED
```

Destination :

```text
INTERMEDIATE.INT_TRIPS__ENRICHED
```

Seules les lignes valides sont conservées :

```sql
rejection_reason IS NULL
```

### Dédoublonnage

Clé métier composite :

```text
vendor_key
pickup_at
dropoff_at
pickup_zone_key
dropoff_zone_key
trip_distance_miles
fare_amount
total_amount
```

Dédoublonnage avec :

```sql
ROW_NUMBER() OVER (...)
QUALIFY ... = 1
```

### `trip_sk`

Créée avec :

```sql
MD5(CONCAT_WS('|', ...))
```

Le même trajet produit donc le même identifiant lors d'un replay.

### Enrichissements

```text
pickup_date
pickup_date_key
pickup_hour
pickup_day_of_week_iso
is_weekend
trip_duration_min
avg_speed_mph
tip_rate_pct
```

---

## 8. `marts/fct_trips.sql`

Source :

```text
INTERMEDIATE.INT_TRIPS__ENRICHED
```

Destination :

```text
MARTS.FCT_TRIPS
```

Grain :

```text
1 ligne = 1 trajet valide
```

La table est alimentée mois par mois avec :

```text
DELETE du mois
+
INSERT du mois
```

Mesures principales :

```text
trip_distance_miles
trip_duration_min
avg_speed_mph
fare_amount
tip_amount
tolls_amount
surcharges_amount
total_amount
tip_rate_pct
```

Le calcul de `surcharges_amount` applique une règle spécifique au fournisseur 1 afin d'éviter le double comptage de certains frais.

---

## 9. Dimensions

### `DIM_VENDOR`

```text
STAGING.VENDOR_CODES
→ MARTS.DIM_VENDOR
```

### `DIM_PAYMENT_TYPE`

```text
STAGING.PAYMENT_TYPE_CODES
→ MARTS.DIM_PAYMENT_TYPE
```

### `DIM_RATE_CODE`

```text
STAGING.RATE_CODE_CODES
→ MARTS.DIM_RATE_CODE
```

### `DIM_ZONE`

```text
STAGING.STG_TLC__TAXI_ZONES
→ MARTS.DIM_ZONE
```

Enrichissements :

```text
is_airport
is_unknown_zone
```

Cette dimension peut être utilisée à la fois pour :

```text
pickup_zone_key
dropoff_zone_key
```

### `DIM_DATE`

Dimension générée à partir de :

```jinja
{{ params.start_month }}
{{ params.end_month }}
```

avec :

```sql
TABLE(GENERATOR(ROWCOUNT => 400))
```

Attributs :

```text
date_key
full_date
year
quarter
month
month_name
day_of_month
day_of_week_iso
day_name
is_weekend
```

Paramètres Airflow identifiés :

```text
start_month
end_month
max_trip_duration_min
max_trip_distance_miles
```

---

## 10. `mart_daily_revenue.sql`

Destination :

```text
MARTS.MART_DAILY_REVENUE
```

Grain :

```text
1 ligne = 1 jour × 1 mode de paiement
```

Sources :

```text
FCT_TRIPS
DIM_DATE
DIM_PAYMENT_TYPE
```

Métriques :

```text
nb_trips
total_revenue
total_fare
total_tips
total_surcharges
avg_revenue_per_trip
total_distance_miles
```

La table est reconstruite entièrement avec :

```sql
CREATE OR REPLACE TABLE
```

---

## 11. `mart_zone_hourly_demand.sql`

Destination :

```text
MARTS.MART_ZONE_HOURLY_DEMAND
```

Grain :

```text
1 ligne
=
1 zone de pickup
×
1 heure
×
1 type de jour
```

Sources :

```text
FCT_TRIPS
DIM_ZONE
```

Métriques :

```text
nb_trips
nb_days
avg_trips_per_day
total_revenue
avg_revenue_per_trip
avg_fare
avg_distance_miles
avg_duration_min
avg_speed_mph
avg_tip_rate_pct_card
revenue_per_hour_driven
```

---

## 12. `mart_data_quality.sql`

Source :

```text
INTERMEDIATE.INT_TRIPS__FLAGGED
```

Destination :

```text
MARTS.MART_DATA_QUALITY
```

La table transforme :

```text
rejection_reason = NULL
```

en :

```text
status = valid
```

Elle calcule :

```text
source_file
source_file_month
status
nb_rows
nb_rows_total
pct_of_file
```

Elle permet de suivre la qualité des fichiers mois par mois.

---

## 13. `controles/raw_mois_charge.sql`

Ce fichier ne transforme aucune donnée.

Il vérifie que le fichier du mois logique est présent dans RAW.

```sql
SELECT COUNT(*) > 0
FROM NYC_TAXI.RAW.YELLOW_TRIPDATA
WHERE _source_file =
    'yellow_tripdata_{{ logical_date.strftime("%Y-%m") }}.parquet';
```

Pour février 2025 :

```text
logical_date.strftime("%Y-%m")
→ 2025-02
```

Le contrôle cherche donc :

```text
yellow_tripdata_2025-02.parquet
```

Il sera utilisé avec :

```text
SQLCheckOperator
```

Si la requête retourne `FALSE`, `0`, `NULL` ou vide, la tâche doit échouer.

---

## 14. Date logique dans les SQL

Deux syntaxes sont utilisées.

```jinja
{{ ds }}
```

donne par exemple :

```text
2025-02-01
```

alors que :

```jinja
{{ logical_date.strftime("%Y-%m") }}
```

donne :

```text
2025-02
```

Les deux reposent sur la date logique du run Airflow.

---

## 15. Graphe de dépendances déduit

```text
COPY INTO RAW
      │
      ▼
raw_mois_charge
      │
      ▼
00_tables
      │
      ├───────────────────────────────┐
      │                               │
      ▼                               ▼
stg_tlc__yellow_trips        stg_tlc__taxi_zones
      │                               │
      ▼                               ▼
int_trips__flagged                 dim_zone
      │
      ├───────────────┐
      │               │
      ▼               ▼
int_trips__enriched  mart_data_quality
      │
      ▼
fct_trips
      │
      ├──────────────→ mart_daily_revenue
      │
      └──────────────→ mart_zone_hourly_demand


codes_tlc
   ├──→ dim_vendor
   ├──→ dim_payment_type
   └──→ dim_rate_code

params start/end
   └──→ dim_date
```

Certaines tâches sont indépendantes.

Par exemple :

```text
codes_tlc
   ├──→ DIM_VENDOR
   ├──→ DIM_PAYMENT_TYPE
   └──→ DIM_RATE_CODE
```

Ces trois dimensions pourront être exécutées en parallèle après `codes_tlc`.

---

# Bilan du Bloc 1 ✅

```text
inventaire des SQL                                     ✅
rôle de STAGING compris                                ✅
rôle de INTERMEDIATE compris                           ✅
rôle de MARTS compris                                  ✅
rôle des contrôles compris                             ✅
idempotence DELETE + INSERT comprise                   ✅
date logique Airflow dans le SQL comprise              ✅
paramètres Jinja identifiés                            ✅
dédoublonnage compris                                  ✅
surrogate key trip_sk comprise                         ✅
star schema identifié                                  ✅
marts analytiques compris                              ✅
graphe de dépendances établi                           ✅
```

Aucune transformation SQL n'a encore été ajoutée au DAG.

---

# Bloc 2 — Ajouter les transformations SQL au DAG ✅

## Objectif

Le Bloc 2 consiste à intégrer les fichiers SQL fournis dans le DAG Airflow principal.

Le principe retenu est :

```text
1 fichier SQL
=
1 tâche Airflow
```

Les tâches sont regroupées par couche avec des `TaskGroup` :

```text
staging
intermediate
marts
```

Les dépendances sont définies en fonction des tables lues et créées par chaque fichier SQL.

---

## 1. Ajout de `template_searchpath`

Le décorateur du DAG a été complété avec :

```python
template_searchpath="/usr/local/airflow/include/sql",
```

Cette option indique à Airflow où rechercher les fichiers SQL.

Il est alors possible d'écrire :

```python
sql="staging/stg_tlc__yellow_trips.sql"
```

au lieu d'utiliser un chemin absolu complet.

Le dossier local :

```text
airflow/include/sql/
```

est disponible dans les conteneurs Astro sous :

```text
/usr/local/airflow/include/sql
```

---

## 2. Ajout des paramètres du DAG

Les paramètres attendus par les fichiers SQL ont été ajoutés au décorateur :

```python
params={
    "max_trip_distance_miles": 100,
    "max_trip_duration_min": 180,
    "start_month": "2025-01-01",
    "end_month": "2025-04-01",
},
```

Ils alimentent les expressions Jinja rencontrées dans les SQL :

```jinja
{{ params.max_trip_distance_miles }}
{{ params.max_trip_duration_min }}
{{ params.start_month }}
{{ params.end_month }}
```

Valeurs utilisées :

```text
max_trip_distance_miles = 100
max_trip_duration_min   = 180
start_month             = 2025-01-01
end_month               = 2025-04-01
```

---

## 3. Imports Airflow ajoutés

Le DAG importe désormais :

```python
from airflow.providers.common.sql.operators.sql import SQLExecuteQueryOperator
from airflow.sdk import TaskGroup, dag, get_current_context, task
```

`SQLExecuteQueryOperator` permet d'exécuter les fichiers SQL dans Snowflake via la connexion Airflow existante :

```text
snowflake_nyc_taxi
```

`TaskGroup` permet de regrouper visuellement les tâches par couche.

`SQLCheckOperator` n'a volontairement pas encore été ajouté : il appartient au Bloc 3 consacré aux contrôles qualité.

---

## 4. Création des tables structurantes

La première tâche SQL ajoutée est :

```python
create_core_tables = SQLExecuteQueryOperator(
    task_id="create_core_tables",
    conn_id=CONN_ID,
    sql="00_tables.sql",
    split_statements=True,
)
```

Elle exécute :

```text
00_tables.sql
```

et crée si nécessaire :

```text
INTERMEDIATE.INT_TRIPS__FLAGGED
INTERMEDIATE.INT_TRIPS__ENRICHED
MARTS.FCT_TRIPS
```

Cette tâche est placée après le chargement RAW.

---

## 5. Groupe `staging`

Les trois fichiers de staging sont regroupés dans :

```python
with TaskGroup(group_id="staging"):
```

Tâches :

```text
staging.stg_tlc__yellow_trips
staging.stg_tlc__taxi_zones
staging.codes_tlc
```

### `stg_tlc__yellow_trips`

```python
stg_yellow_trips = SQLExecuteQueryOperator(
    task_id="stg_tlc__yellow_trips",
    conn_id=CONN_ID,
    sql="staging/stg_tlc__yellow_trips.sql",
    split_statements=True,
)
```

### `stg_tlc__taxi_zones`

```python
stg_taxi_zones = SQLExecuteQueryOperator(
    task_id="stg_tlc__taxi_zones",
    conn_id=CONN_ID,
    sql="staging/stg_tlc__taxi_zones.sql",
    split_statements=True,
)
```

### `codes_tlc`

```python
codes_tlc = SQLExecuteQueryOperator(
    task_id="codes_tlc",
    conn_id=CONN_ID,
    sql="staging/codes_tlc.sql",
    split_statements=True,
)
```

Ces tâches sont indépendantes entre elles et peuvent donc être exécutées en parallèle.

---

## 6. Groupe `intermediate`

Les deux fichiers intermédiaires sont regroupés dans :

```python
with TaskGroup(group_id="intermediate"):
```

Tâches :

```text
intermediate.int_trips__flagged
intermediate.int_trips__enriched
```

### `int_trips__flagged`

```python
int_trips_flagged = SQLExecuteQueryOperator(
    task_id="int_trips__flagged",
    conn_id=CONN_ID,
    sql="intermediate/int_trips__flagged.sql",
    split_statements=True,
)
```

### `int_trips__enriched`

```python
int_trips_enriched = SQLExecuteQueryOperator(
    task_id="int_trips__enriched",
    conn_id=CONN_ID,
    sql="intermediate/int_trips__enriched.sql",
    split_statements=True,
)
```

Dépendance :

```text
int_trips__flagged
        ↓
int_trips__enriched
```

Code :

```python
int_trips_flagged >> int_trips_enriched
```

---

## 7. Groupe `marts`

Les neuf tâches de la couche analytique sont regroupées dans :

```python
with TaskGroup(group_id="marts"):
```

Tâches :

```text
marts.dim_date
marts.dim_payment_type
marts.dim_rate_code
marts.dim_vendor
marts.dim_zone
marts.fct_trips
marts.mart_daily_revenue
marts.mart_data_quality
marts.mart_zone_hourly_demand
```

### Dimensions

```python
dim_date
dim_payment_type
dim_rate_code
dim_vendor
dim_zone
```

### Table de faits

```python
fct_trips
```

### Data marts

```python
mart_daily_revenue
mart_data_quality
mart_zone_hourly_demand
```

---

## 8. Utilisation de `split_statements=True`

Toutes les tâches SQL utilisent :

```python
split_statements=True
```

Cette option est indispensable pour les fichiers contenant plusieurs instructions.

Exemples :

```text
00_tables.sql
→ plusieurs CREATE TABLE

int_trips__flagged.sql
→ DELETE
→ INSERT

int_trips__enriched.sql
→ DELETE
→ INSERT

fct_trips.sql
→ DELETE
→ INSERT
```

Sur les fichiers ne contenant qu'une seule instruction, cette option ne modifie pas le comportement.

---

## 9. Dépendances après le chargement RAW

Le résultat de la tâche Python :

```text
copy_into_raw
```

est utilisé comme point de départ des transformations :

```python
raw_loaded = copy_into_raw(staged_file)
```

Puis :

```python
raw_loaded >> create_core_tables
```

Flux :

```text
download_and_put
      ↓
copy_into_raw
      ↓
create_core_tables
```

---

## 10. Dépendances STAGING

Une fois les tables structurantes créées :

```python
create_core_tables >> [
    stg_yellow_trips,
    stg_taxi_zones,
    codes_tlc,
    dim_date,
]
```

Les branches indépendantes peuvent démarrer en parallèle.

---

## 11. Branche trajets

Dépendances :

```text
STG_TLC__YELLOW_TRIPS
        ↓
INT_TRIPS__FLAGGED
        ↓
INT_TRIPS__ENRICHED
        ↓
FCT_TRIPS
```

Code :

```python
stg_yellow_trips >> int_trips_flagged
int_trips_enriched >> fct_trips
```

La dépendance :

```text
int_trips_flagged → int_trips_enriched
```

est définie à l'intérieur du `TaskGroup intermediate`.

---

## 12. Branche zones

Dépendances :

```text
STG_TLC__TAXI_ZONES
        ↓
DIM_ZONE
```

Code :

```python
stg_taxi_zones >> dim_zone
```

---

## 13. Branche codes TLC

Dépendances :

```text
codes_tlc
   ├──→ dim_vendor
   ├──→ dim_payment_type
   └──→ dim_rate_code
```

Code :

```python
codes_tlc >> [
    dim_vendor,
    dim_payment_type,
    dim_rate_code,
]
```

Les trois dimensions peuvent être calculées en parallèle.

---

## 14. Branche dimension date

`DIM_DATE` ne dépend pas d'une table métier.

Elle dépend uniquement des paramètres du DAG :

```text
start_month
end_month
```

Elle peut donc être construite dès que l'étape de préparation des tables est terminée.

```text
create_core_tables
        ↓
dim_date
```

---

## 15. Mart de qualité

`MART_DATA_QUALITY` lit directement :

```text
INT_TRIPS__FLAGGED
```

Dépendance :

```python
int_trips_flagged >> mart_data_quality
```

Il n'est pas nécessaire d'attendre `INT_TRIPS__ENRICHED` ou `FCT_TRIPS`.

---

## 16. Mart quotidien de chiffre d'affaires

`MART_DAILY_REVENUE` dépend de :

```text
FCT_TRIPS
DIM_DATE
DIM_PAYMENT_TYPE
```

Code :

```python
[
    fct_trips,
    dim_date,
    dim_payment_type,
] >> mart_daily_revenue
```

La tâche ne démarre que lorsque ses trois sources sont prêtes.

---

## 17. Mart de demande horaire par zone

`MART_ZONE_HOURLY_DEMAND` dépend de :

```text
FCT_TRIPS
DIM_ZONE
```

Code :

```python
[
    fct_trips,
    dim_zone,
] >> mart_zone_hourly_demand
```

---

## 18. Graphe logique obtenu

```text
copy_into_raw
      │
      ▼
create_core_tables
      │
      ├───────────────────────┬───────────────────────┬─────────────────┐
      │                       │                       │                 │
      ▼                       ▼                       ▼                 ▼
stg_yellow_trips       stg_taxi_zones           codes_tlc         dim_date
      │                       │                       │
      ▼                       ▼                       ├──→ dim_vendor
int_trips_flagged          dim_zone                  ├──→ dim_payment_type
      │                       │                       └──→ dim_rate_code
      ├───────────────┐       │
      │               │       │
      ▼               ▼       │
int_trips_enriched  mart_data_quality
      │
      ▼
fct_trips
      │
      ├──────────────┬─────────────────┐
      │              │                 │
      │        dim_payment_type        │
      │              │                 │
      │              └──────┐          │
      │                     ▼          │
      ├────────────→ mart_daily_revenue │
      │                                │
      └───────────────┬────────────────┘
                      │
                   dim_zone
                      │
                      ▼
           mart_zone_hourly_demand
```

Le graphe ne force pas artificiellement toutes les tâches à s'exécuter en série.

Les branches indépendantes peuvent fonctionner en parallèle.

---

## 19. Validation des imports

Commande :

```bash
cd airflow
astro dev run dags list-import-errors
```

Résultat :

```text
No data found
```

Cela confirme qu'Airflow ne détecte aucune erreur d'import dans le DAG.

Les warnings observés :

```text
Astro managed secrets backend is disabled
FileType is deprecated
Could not import graphviz
```

étaient non bloquants.

---

## 20. Validation des tâches enregistrées

Commande :

```bash
astro dev run tasks list nyc_taxi_monthly
```

Résultat :

```text
build_file_name
check_file_exists
copy_into_raw
create_core_tables
download_and_put
intermediate.int_trips__enriched
intermediate.int_trips__flagged
marts.dim_date
marts.dim_payment_type
marts.dim_rate_code
marts.dim_vendor
marts.dim_zone
marts.fct_trips
marts.mart_daily_revenue
marts.mart_data_quality
marts.mart_zone_hourly_demand
staging.codes_tlc
staging.stg_tlc__taxi_zones
staging.stg_tlc__yellow_trips
```

Airflow reconnaît donc les 19 tâches du DAG.

Répartition :

```text
4 tâches ingestion Python
1 tâche de création des tables
3 tâches STAGING
2 tâches INTERMEDIATE
9 tâches MARTS
```

Total :

```text
19 tâches
```

---

## 21. Vérification de la commande `--tree`

Une tentative de visualisation CLI a été faite avec :

```bash
astro dev run tasks list nyc_taxi_monthly --tree
```

La commande a échoué car cette option n'existe pas dans la version Airflow utilisée.

Vérification :

```bash
astro dev run tasks list --help
```

Options disponibles :

```text
-B / --bundle-name
-v / --verbose
```

Il n'y a donc pas de :

```text
--tree
```

Cette erreur ne vient pas du DAG.

La validation du Bloc 2 repose sur :

```text
list-import-errors → aucune erreur
tasks list         → 19 tâches présentes
```

---

# Bilan du Bloc 2 ✅

```text
template_searchpath ajouté                            ✅
paramètres du DAG ajoutés                             ✅
SQLExecuteQueryOperator importé                       ✅
TaskGroup importé                                     ✅
00_tables.sql intégré                                 ✅
TaskGroup STAGING créé                                ✅
TaskGroup INTERMEDIATE créé                           ✅
TaskGroup MARTS créé                                  ✅
toutes les tâches SQL créées                          ✅
split_statements=True configuré                       ✅
dépendances définies selon FROM / JOIN                ✅
branches parallèles conservées                        ✅
aucune erreur d'import Airflow                        ✅
19 tâches reconnues par Airflow                       ✅
```

Le Bloc 2 est terminé.

Aucune exécution historique n'a encore été rejouée.

Les runs de janvier, février et mars restent volontairement inchangés pour éviter de relancer le pipeline avant l'ajout des contrôles qualité du Bloc 3.



---

# Bloc 3 — Ajouter les contrôles de qualité ✅

## Objectif

Le Bloc 3 consiste à ajouter des contrôles de qualité dans le DAG afin de bloquer le pipeline si les données ne respectent pas les règles attendues.

Trois contrôles sont désormais intégrés :

```text
1. vérifier que le mois est bien chargé dans RAW
2. vérifier que le taux de rejet reste acceptable
3. vérifier qu'il n'existe aucun doublon dans FCT_TRIPS
```

Les contrôles utilisent :

```python
SQLCheckOperator
```

avec :

```python
retries=0
```

L'objectif est qu'un contrôle en échec bloque immédiatement les traitements situés en aval.

---

## 1. Import de `SQLCheckOperator`

L'import Airflow a été complété :

```python
from airflow.providers.common.sql.operators.sql import (
    SQLCheckOperator,
    SQLExecuteQueryOperator,
)
```

`SQLCheckOperator` exécute une requête SQL qui doit renvoyer une valeur vraie.

Exemples de valeurs considérées comme invalides :

```text
FALSE
0
NULL
valeur vide
```

Dans ce cas, la tâche Airflow passe en échec et les tâches dépendantes ne sont pas exécutées.

---

## 2. Contrôle RAW : `raw_mois_charge.sql`

Le premier contrôle était fourni dans le starter kit :

```text
airflow/include/sql/controles/raw_mois_charge.sql
```

Contenu :

```sql
-- Le mois traité est bien présent dans RAW.
SELECT COUNT(*) > 0
FROM NYC_TAXI.RAW.YELLOW_TRIPDATA
WHERE _source_file =
    'yellow_tripdata_{{ logical_date.strftime("%Y-%m") }}.parquet';
```

Exemple pour février 2025 :

```text
logical_date.strftime("%Y-%m")
→ 2025-02
```

Le contrôle recherche donc :

```text
yellow_tripdata_2025-02.parquet
```

La tâche Airflow ajoutée est :

```python
check_raw_month_loaded = SQLCheckOperator(
    task_id="check_raw_month_loaded",
    conn_id=CONN_ID,
    sql="controles/raw_mois_charge.sql",
    retries=0,
)
```

Elle est placée juste après le chargement RAW :

```python
raw_loaded >> check_raw_month_loaded >> create_core_tables
```

Flux :

```text
copy_into_raw
      ↓
check_raw_month_loaded
      ↓
create_core_tables
```

Ainsi, si le fichier du mois n'est pas présent en RAW, aucune transformation SQL ne démarre.

---

## 3. Contrôle des doublons dans `FCT_TRIPS`

Un nouveau fichier a été créé :

```text
airflow/include/sql/controles/trips_no_duplicates.sql
```

Contenu :

```sql
-- Le mois traité ne doit contenir aucun trajet en double.
SELECT COUNT(*) = COUNT(DISTINCT trip_sk)
FROM NYC_TAXI.MARTS.FCT_TRIPS
WHERE source_file_month = '{{ ds }}'::date;
```

Le principe est :

```text
nombre total de lignes
=
nombre de trip_sk distincts
```

Si les deux valeurs sont différentes :

```text
au moins un doublon existe
→ FALSE
→ contrôle Airflow en échec
```

La tâche Airflow est :

```python
check_trips_no_duplicates = SQLCheckOperator(
    task_id="check_trips_no_duplicates",
    conn_id=CONN_ID,
    sql="controles/trips_no_duplicates.sql",
    retries=0,
)
```

Elle est placée après :

```text
MARTS.FCT_TRIPS
```

Dépendance :

```python
fct_trips >> check_trips_no_duplicates
```

Les marts qui exploitent la table de faits attendent ensuite la réussite de ce contrôle.

Pour le mart quotidien :

```python
[
    check_trips_no_duplicates,
    dim_date,
    dim_payment_type,
] >> mart_daily_revenue
```

Pour le mart de demande horaire :

```python
[
    check_trips_no_duplicates,
    dim_zone,
] >> mart_zone_hourly_demand
```

Flux :

```text
FCT_TRIPS
    ↓
check_trips_no_duplicates
    ├──→ MART_DAILY_REVENUE
    └──→ MART_ZONE_HOURLY_DEMAND
```

---

## 4. Contrôle du taux de rejet

Un second contrôle personnalisé a été ajouté :

```text
airflow/include/sql/controles/rejection_rate.sql
```

Le seuil retenu est :

```text
10 %
```

Il est paramétré dans le DAG :

```python
params={
    "max_trip_distance_miles": 100,
    "max_trip_duration_min": 180,
    "start_month": "2025-01-01",
    "end_month": "2025-04-01",
    "max_rejection_pct": 10,
},
```

Cette valeur n'est donc pas codée en dur dans le fichier SQL.

---

## 5. SQL du contrôle du taux de rejet

Contenu :

```sql
-- Le pourcentage de trajets rejetés du mois doit rester sous le seuil autorisé.
SELECT
    COALESCE(
        100.0 * COUNT_IF(rejection_reason IS NOT NULL)
        / NULLIF(COUNT(*), 0),
        100.0
    ) <= {{ params.max_rejection_pct }}
FROM NYC_TAXI.INTERMEDIATE.INT_TRIPS__FLAGGED
WHERE source_file_month = '{{ ds }}'::date;
```

Calcul effectué :

```text
nombre de trajets rejetés
────────────────────────── × 100
nombre total de trajets
```

Le résultat doit être :

```text
<= 10 %
```

### `NULLIF`

```sql
NULLIF(COUNT(*), 0)
```

évite une division par zéro.

### `COALESCE`

```sql
COALESCE(..., 100.0)
```

permet de considérer un mois vide comme une anomalie.

Si aucune ligne n'est disponible :

```text
taux utilisé = 100 %
```

Le contrôle échoue donc avec le seuil normal de 10 %.

---

## 6. Placement dans la couche INTERMEDIATE

Le contrôle est créé dans :

```python
with TaskGroup(group_id="intermediate"):
```

Tâche :

```python
check_rejection_rate = SQLCheckOperator(
    task_id="check_rejection_rate",
    conn_id=CONN_ID,
    sql="controles/rejection_rate.sql",
    retries=0,
)
```

La chaîne est :

```python
int_trips_flagged >> check_rejection_rate >> int_trips_enriched
```

Flux :

```text
STG_TLC__YELLOW_TRIPS
          ↓
INT_TRIPS__FLAGGED
          ↓
check_rejection_rate
          ↓
INT_TRIPS__ENRICHED
          ↓
FCT_TRIPS
```

Cela garantit que les données enrichies ne sont générées que si la proportion de trajets rejetés reste dans le seuil autorisé.

---

## 7. Dépendance du mart de qualité

`MART_DATA_QUALITY` dépend désormais également de la réussite du contrôle :

```python
check_rejection_rate >> mart_data_quality
```

Flux :

```text
INT_TRIPS__FLAGGED
          ↓
check_rejection_rate
       ┌──┴───────────┐
       ↓              ↓
INT_TRIPS__ENRICHED  MART_DATA_QUALITY
```

Cette organisation sera utile au Bloc 4 pour vérifier qu'un contrôle en échec bloque correctement les traitements situés en aval.

---

## 8. Graphe des contrôles qualité

Le pipeline contient désormais trois barrières qualité principales :

```text
copy_into_raw
      │
      ▼
check_raw_month_loaded
      │
      ▼
create_core_tables
      │
      ▼
STAGING
      │
      ▼
INT_TRIPS__FLAGGED
      │
      ▼
check_rejection_rate
      │
      ▼
INT_TRIPS__ENRICHED
      │
      ▼
FCT_TRIPS
      │
      ▼
check_trips_no_duplicates
      │
      ├──→ MART_DAILY_REVENUE
      │
      └──→ MART_ZONE_HOURLY_DEMAND
```

Les contrôles sont donc placés juste après la donnée qu'ils vérifient et avant les traitements qui utilisent cette donnée.

---

## 9. Validation Airflow

Après ajout des contrôles :

```bash
astro dev run dags list-import-errors
```

Résultat :

```text
No data found
```

Le DAG ne contient donc aucune erreur d'import.

Vérification des tâches :

```bash
astro dev run tasks list nyc_taxi_monthly | grep check
```

Résultat :

```text
check_file_exists
check_raw_month_loaded
intermediate.check_rejection_rate
marts.check_trips_no_duplicates
```

`check_file_exists` correspond à la vérification HTTP déjà présente lors de l'ingestion.

Les trois contrôles SQL du Bloc 3 sont :

```text
check_raw_month_loaded
intermediate.check_rejection_rate
marts.check_trips_no_duplicates
```

Après ajout des trois contrôles SQL, le DAG contient au total :

```text
22 tâches
```

Les 19 tâches recensées au Bloc 2 correspondaient à l'état du DAG avant l'ajout de ces trois contrôles.

---

## 10. Pourquoi `retries=0`

Les trois contrôles SQL utilisent :

```python
retries=0
```

Un contrôle qualité vérifie l'état actuel des données.

Si la donnée est invalide, relancer automatiquement la même requête quelques minutes plus tard ne corrige rien.

Sans `retries=0`, Airflow pourrait laisser inutilement la tâche en :

```text
up_for_retry
```

avant de finalement la marquer en échec.

Avec :

```python
retries=0
```

le contrôle échoue immédiatement.

---

# Bilan du Bloc 3 ✅

```text
SQLCheckOperator importé                           ✅
contrôle RAW fourni intégré                        ✅
contrôle absence de doublons créé                  ✅
contrôle taux maximum de rejet créé                ✅
seuil max_rejection_pct paramétré à 10 %           ✅
retries=0 sur tous les contrôles                   ✅
contrôle RAW placé après COPY INTO                 ✅
contrôle rejet placé après INT_TRIPS__FLAGGED      ✅
contrôle doublons placé après FCT_TRIPS             ✅
tâches aval dépendantes des contrôles              ✅
aucune erreur d'import Airflow                     ✅
trois contrôles SQL reconnus par Airflow           ✅
```

Le Bloc 3 est terminé.

Aucun ancien run n'a encore été rejoué.

La prochaine étape consiste à répondre à l'exigence du brief :

```text
provoquer volontairement l'échec d'un contrôle
```

Le contrôle retenu sera :

```text
intermediate.check_rejection_rate
```

Le paramètre :

```text
max_rejection_pct = 10
```

sera temporairement durci à :

```text
max_rejection_pct = 0
```

afin de vérifier que les tâches situées en aval ne s'exécutent pas.



---

# Bloc 4 — Tester volontairement un échec ✅

## Objectif

Le brief demande de vérifier qu'un contrôle qualité en échec bloque bien les tâches situées en aval.

Le contrôle choisi est :

```text
intermediate.check_rejection_rate
```

En fonctionnement normal, le DAG utilise :

```python
"max_rejection_pct": 10,
```

Pour provoquer volontairement un échec, le seuil a été temporairement durci à :

```python
"max_rejection_pct": 0,
```

Avec ce seuil, le pipeline exige artificiellement :

```text
0 % de trajets rejetés
```

Dès qu'au moins un trajet du mois est rejeté, le contrôle doit donc échouer.

---

## 1. Modification temporaire du seuil

Le paramètre du DAG a temporairement été modifié :

```python
params={
    "max_trip_distance_miles": 100,
    "max_trip_duration_min": 180,
    "start_month": "2025-01-01",
    "end_month": "2025-04-01",
    "max_rejection_pct": 0,
},
```

Cette modification ne change pas la logique SQL.

Elle modifie uniquement la valeur utilisée dans :

```jinja
{{ params.max_rejection_pct }}
```

dans :

```text
controles/rejection_rate.sql
```

---

## 2. Validation du DAG avec le seuil de test

Commande :

```bash
astro dev run dags list-import-errors
```

Résultat :

```text
No data found
```

Le DAG restait donc valide avec le seuil temporaire à `0`.

---

## 3. Rejeu des runs existants

Les DagRuns de janvier, février et mars existaient déjà avant l'ajout des nouvelles tâches SQL et des contrôles.

Ils ont été rejoués afin de créer et exécuter les nouvelles Task Instances.

Vérification des runs :

```bash
astro dev run dags list-runs nyc_taxi_monthly
```

État observé pendant le test :

```text
2025-01 → failed
2025-02 → failed
2025-03 → failed
```

Ce résultat était cohérent avec le seuil volontairement impossible de `0 %`.

---

## 4. Vérification détaillée du run de février

Le run contrôlé est :

```text
scheduled__2025-02-01T00:00:00+00:00
```

Commande utilisée :

```bash
astro dev run tasks states-for-dag-run \
  nyc_taxi_monthly \
  'scheduled__2025-02-01T00:00:00+00:00'
```

Cette commande affiche l'état exact de toutes les Task Instances du run.

---

## 5. Résultats observés avant le contrôle

Les tâches d'ingestion et de préparation ont réussi :

```text
build_file_name                    → success
check_file_exists                  → success
download_and_put                   → success
copy_into_raw                      → success
check_raw_month_loaded             → success
create_core_tables                 → success
staging.stg_tlc__yellow_trips      → success
staging.stg_tlc__taxi_zones        → success
staging.codes_tlc                  → success
```

Les dimensions indépendantes ont également pu être construites :

```text
marts.dim_date                     → success
marts.dim_payment_type             → success
marts.dim_rate_code                → success
marts.dim_vendor                   → success
marts.dim_zone                     → success
```

Cela montre qu'Airflow n'arrête pas arbitrairement tout le DAG : seules les branches dépendantes du contrôle en échec sont bloquées.

---

## 6. Échec volontaire du quality gate

La tâche qui prépare les trajets avec leur motif de rejet a réussi :

```text
intermediate.int_trips__flagged
→ success
```

Le contrôle a ensuite échoué comme prévu :

```text
intermediate.check_rejection_rate
→ failed
```

Le comportement testé est donc :

```text
INT_TRIPS__FLAGGED
        ↓
check_rejection_rate
        ↓
      FAILED
```

Le contrôle utilise :

```python
retries=0
```

Il n'a donc pas attendu de retry inutile avant de passer en échec.

---

## 7. Blocage des tâches en aval

Les tâches dépendant du contrôle sont passées en :

```text
upstream_failed
```

États observés pour février :

```text
intermediate.int_trips__enriched   → upstream_failed
marts.mart_data_quality            → upstream_failed
marts.fct_trips                    → upstream_failed
marts.check_trips_no_duplicates    → upstream_failed
marts.mart_daily_revenue           → upstream_failed
marts.mart_zone_hourly_demand      → upstream_failed
```

Le graphe testé est donc :

```text
INT_TRIPS__FLAGGED
        │
        ▼
check_rejection_rate
        │
        ▼
      FAILED
       / \\
      /   \\
     ▼     ▼
INT_TRIPS__ENRICHED    MART_DATA_QUALITY
upstream_failed        upstream_failed
     │
     ▼
FCT_TRIPS
upstream_failed
     │
     ▼
check_trips_no_duplicates
upstream_failed
     │
     ├──→ MART_DAILY_REVENUE
     │    upstream_failed
     │
     └──→ MART_ZONE_HOURLY_DEMAND
          upstream_failed
```

Le contrôle joue donc bien le rôle de :

```text
quality gate
```

Une donnée considérée comme de mauvaise qualité n'est pas propagée vers les couches suivantes.

---

## 8. Parallélisme conservé

Les dimensions suivantes sont restées en `success` :

```text
DIM_DATE
DIM_PAYMENT_TYPE
DIM_RATE_CODE
DIM_VENDOR
DIM_ZONE
```

Elles ne dépendent pas de :

```text
check_rejection_rate
```

Leur exécution réussie est donc normale.

Cela confirme que les dépendances du DAG sont suffisamment fines : un contrôle en échec bloque uniquement les branches qui dépendent réellement de lui.

---

## 9. Restauration du seuil normal

Une fois le test terminé, le paramètre a été restauré à :

```python
"max_rejection_pct": 10,
```

Le seuil à `0` n'était qu'un réglage temporaire destiné à tester le comportement du DAG.

---

## 10. Validation après restauration

Commande :

```bash
astro dev run dags list-import-errors
```

Résultat :

```text
No data found
```

Le DAG est donc revenu dans sa configuration normale et reste valide.

---

# Bilan du Bloc 4 ✅

```text
seuil temporairement abaissé à 0 %                  ✅
DAG valide avec le seuil de test                    ✅
run de février vérifié                              ✅
INT_TRIPS__FLAGGED exécutée avec succès             ✅
check_rejection_rate volontairement en échec        ✅
tâches en aval bloquées                             ✅
état upstream_failed vérifié                        ✅
branches indépendantes toujours exécutables         ✅
seuil normal de 10 % restauré                       ✅
DAG valide après restauration                       ✅
```

Le Bloc 4 est terminé.

Le prochain objectif est de rejouer février avec le seuil normal afin de vérifier :

```text
- que le pipeline passe entièrement ;
- que le nombre de lignes reste identique après replay ;
- qu'aucun doublon n'est créé.
```


---

# Bloc 5 — Rejouer février et vérifier l'idempotence ✅

## Objectif

Le Bloc 5 doit démontrer qu'un mois déjà traité peut être rejoué sans provoquer d'accumulation de lignes ni de doublons.

Le mois utilisé pour cette vérification est :

```text
février 2025
```

Le mécanisme d'idempotence des tables mensuelles repose sur :

```text
DELETE du mois
+
INSERT du mois recalculé
```

---

## 1. Premier replay avec le seuil normal

Après le test volontaire du Bloc 4, le paramètre a été restauré à :

```python
"max_rejection_pct": 10,
```

Les 22 Task Instances du run suivant ont été réinitialisées :

```text
scheduled__2025-02-01T00:00:00+00:00
```

Le replay n'a cependant pas abouti normalement.

État observé :

```text
intermediate.int_trips__flagged   → success
intermediate.check_rejection_rate → failed
intermediate.int_trips__enriched  → upstream_failed
marts.fct_trips                    → upstream_failed
```

Le seuil de `10 %` n'était donc pas la cause du problème : il révélait une anomalie réelle dans les données chargées.

---

## 2. Diagnostic du taux de rejet anormal

Un contrôle dans Snowflake a montré pour février :

```text
total_rows    = 3 577 543
rejected_rows = 3 577 543
valid_rows    = 0
rejection_pct = 100 %
```

La répartition des motifs de rejet était :

```text
duration_too_long       = 3 572 379  (99,86 %)
duration_non_positive   =     5 164  ( 0,14 %)
```

Le fichier SQL `intermediate/int_trips__flagged.sql` a alors été contrôlé.

La règle de durée était correcte :

```sql
WHEN DATEDIFF('second', pickup_at, dropoff_at)
     > {{ params.max_trip_duration_min }} * 60
THEN 'duration_too_long'
```

Aucune modification des transformations SQL fournies n'était donc nécessaire.

---

## 3. Inspection des timestamps

Un échantillon de la vue de staging a révélé des durées absurdes.

Exemple avant correction :

```text
DURATION_SECONDS = 1 214 996 400
DURATION_MINUTES = 20 249 940
```

Ces valeurs correspondaient en réalité à des timestamps Parquet dont l'unité logique n'était pas correctement interprétée.

Le `FILE FORMAT` Snowflake a été inspecté avec :

```sql
DESC FILE FORMAT NYC_TAXI.RAW.PARQUET_FF;
```

Résultat :

```text
USE_LOGICAL_TYPE = false
```

Le format Parquet n'utilisait donc pas les logical types présents dans le fichier source pour interpréter correctement les timestamps.

---

## 4. Correction du format Parquet

Le `FILE FORMAT` a été corrigé :

```sql
ALTER FILE FORMAT NYC_TAXI.RAW.PARQUET_FF
SET USE_LOGICAL_TYPE = TRUE;
```

Vérification :

```text
USE_LOGICAL_TYPE = true
```

Cette modification ne corrigeant pas rétroactivement les lignes déjà chargées dans `RAW`, le mois de février a dû être rechargé.

---

## 5. Rechargement ponctuel de février

Les lignes du fichier de février ont d'abord été supprimées :

```sql
DELETE FROM NYC_TAXI.RAW.YELLOW_TRIPDATA
WHERE _source_file = 'yellow_tripdata_2025-02.parquet';
```

Puis le fichier déjà présent dans le stage a été rechargé avec le format corrigé :

```sql
COPY INTO NYC_TAXI.RAW.YELLOW_TRIPDATA
FROM @NYC_TAXI.RAW.NYC_TAXI_STAGE
FILES = ('yellow_tripdata_2025-02.parquet')
FILE_FORMAT = (
    FORMAT_NAME = NYC_TAXI.RAW.PARQUET_FF
)
MATCH_BY_COLUMN_NAME = CASE_INSENSITIVE
INCLUDE_METADATA = (
    _source_file = METADATA$FILENAME,
    _loaded_at = METADATA$START_SCAN_TIME
)
FORCE = TRUE
ON_ERROR = ABORT_STATEMENT;
```

Résultat :

```text
status      = LOADED
rows_parsed = 3 577 543
rows_loaded = 3 577 543
errors_seen = 0
```

`FORCE = TRUE` n'a été utilisé que pour cette opération ponctuelle de réparation, car Snowflake connaissait déjà le fichier dans son historique de chargement.

Il n'a pas été ajouté au fonctionnement normal du DAG afin de conserver l'idempotence de l'ingestion.

---

## 6. Validation des timestamps après correction

Un nouvel échantillon de la vue de staging a donné des valeurs réalistes :

```text
2025-02-01 16:49:17 → 2025-02-01 16:52:15 →  2,97 min
2025-02-01 16:58:44 → 2025-02-01 17:25:09 → 26,42 min
2025-02-01 16:53:31 → 2025-02-01 17:28:07 → 34,60 min
2025-02-01 16:40:49 → 2025-02-01 17:41:24 → 60,58 min
```

Le problème venait donc bien du chargement Parquet et non des règles de transformation.

---

## 7. Replay complet de février après correction

Les 22 Task Instances du run de février ont ensuite été réinitialisées.

Commande de contrôle :

```bash
astro dev run tasks states-for-dag-run \
  nyc_taxi_monthly \
  'scheduled__2025-02-01T00:00:00+00:00'
```

Toutes les tâches sont revenues en `success`, notamment :

```text
check_raw_month_loaded                 → success
intermediate.int_trips__flagged        → success
intermediate.check_rejection_rate      → success
intermediate.int_trips__enriched       → success
marts.fct_trips                        → success
marts.check_trips_no_duplicates        → success
marts.mart_data_quality                → success
marts.mart_daily_revenue               → success
marts.mart_zone_hourly_demand          → success
```

Le contrôle du taux de rejet passe donc avec le seuil normal de `10 %` lorsque les timestamps sont correctement chargés.

---

## 8. Baseline avant test d'idempotence

Après cette première exécution réussie, les volumes de février ont été relevés :

```text
INT_TRIPS__FLAGGED  = 3 577 543
INT_TRIPS__ENRICHED = 3 305 246
FCT_TRIPS           = 3 305 246
```

Ces valeurs constituent la baseline avant un second replay du même mois.

---

## 9. Second replay de février

Les 22 Task Instances du même run ont été réinitialisées une nouvelle fois, sans modifier les données ni les paramètres.

Après ce second replay, les mêmes requêtes de comptage donnent :

```text
INT_TRIPS__FLAGGED  = 3 577 543
INT_TRIPS__ENRICHED = 3 305 246
FCT_TRIPS           = 3 305 246
```

Comparaison :

```text
                         avant replay     après replay
INT_TRIPS__FLAGGED        3 577 543        3 577 543
INT_TRIPS__ENRICHED       3 305 246        3 305 246
FCT_TRIPS                 3 305 246        3 305 246
```

Aucune accumulation de lignes n'a été observée.

Le contrôle :

```text
marts.check_trips_no_duplicates
```

est également resté en `success`.

---

# Bilan du Bloc 5 ✅

```text
seuil normal de 10 % restauré                         ✅
anomalie de rejet détectée                            ✅
SQL de transformation vérifié                         ✅
cause identifiée dans le FILE FORMAT Parquet          ✅
USE_LOGICAL_TYPE passé à TRUE                         ✅
février rechargé sans erreur                          ✅
timestamps redevenus cohérents                        ✅
pipeline février entièrement en success               ✅
baseline relevée avant replay                         ✅
second replay effectué                                ✅
volumes strictement identiques                        ✅
contrôle de doublons passant                          ✅
idempotence démontrée                                 ✅
```

Le Bloc 5 est terminé.

---

# Bloc 6 — Validation finale du Jour 4 ✅

## Objectif

Le Bloc 6 consiste à remettre les trois mois dans un état cohérent puis à valider les résultats finaux attendus par le brief.

---

## 1. Vérification de janvier et mars

Janvier et mars avaient été chargés avant la correction de `USE_LOGICAL_TYPE`.

Un contrôle a confirmé qu'ils présentaient le même problème que février :

```text
SOURCE_FILE_MONTH  TOTAL_ROWS  DURATION_NON_POSITIVE  DURATION_TOO_LONG
2025-01-01          3 475 226                   2 051          3 473 175
2025-03-01          4 145 257                  22 280          4 122 977
```

La quasi-totalité des trajets était donc artificiellement classée en `duration_too_long`.

---

## 2. Rechargement de janvier et mars

Les lignes correspondant aux deux fichiers ont été supprimées de la RAW puis les Parquet ont été rechargés avec le `FILE FORMAT` corrigé.

Résultat du `COPY INTO` :

```text
yellow_tripdata_2025-01.parquet
status      = LOADED
rows_parsed = 3 475 226
rows_loaded = 3 475 226
errors_seen = 0

yellow_tripdata_2025-03.parquet
status      = LOADED
rows_parsed = 4 145 257
rows_loaded = 4 145 257
errors_seen = 0
```

À ce stade, les trois mois de la RAW utilisent tous la même interprétation correcte des timestamps Parquet.

---

## 3. Rejeu de janvier et mars dans Airflow

Les runs de janvier et mars ont été réinitialisés afin de recalculer les couches :

```text
STAGING
  ↓
INTERMEDIATE
  ↓
MARTS
```

Commande de validation :

```bash
astro dev run dags list-runs nyc_taxi_monthly
```

Résultat final :

```text
scheduled__2025-03-01T00:00:00+00:00 → success
scheduled__2025-02-01T00:00:00+00:00 → success
scheduled__2025-01-01T00:00:00+00:00 → success
```

Les trois exécutions demandées par le brief sont donc en `success`.

---

## 4. Volumes finaux de `FCT_TRIPS`

Comptage par mois :

```sql
SELECT
    source_file_month,
    COUNT(*) AS trip_count
FROM NYC_TAXI.MARTS.FCT_TRIPS
WHERE source_file_month >= '2025-01-01'::date
  AND source_file_month < '2025-04-01'::date
GROUP BY source_file_month
ORDER BY source_file_month;
```

Résultat :

```text
2025-01-01 → 3 251 337
2025-02-01 → 3 305 246
2025-03-01 → 3 825 795
```

Total :

```sql
SELECT COUNT(*) AS total_valid_trips
FROM NYC_TAXI.MARTS.FCT_TRIPS
WHERE source_file_month >= '2025-01-01'::date
  AND source_file_month < '2025-04-01'::date;
```

Résultat :

```text
TOTAL_VALID_TRIPS = 10 382 378
```

Le résultat correspond exactement à la valeur attendue par le brief :

```text
10 382 378 trajets valides
```

---

## 5. Contrôles qualité finaux

Les trois quality gates intégrés au pipeline sont opérationnels :

```text
check_raw_month_loaded
intermediate.check_rejection_rate
marts.check_trips_no_duplicates
```

Le test volontaire du Bloc 4 a démontré qu'un contrôle en échec bloque bien les tâches qui en dépendent.

Les exécutions finales démontrent ensuite que les trois contrôles passent avec les données corrigées.

---

## 6. Validation des exigences du Jour 4

```text
lecture et compréhension des SQL fournis                 ✅
ordre des dépendances déduit                             ✅
une tâche Airflow par fichier SQL                        ✅
TaskGroups STAGING / INTERMEDIATE / MARTS                ✅
contrôle RAW fourni intégré                              ✅
deux contrôles supplémentaires créés                    ✅
retries=0 sur les contrôles                              ✅
échec volontaire d'un quality gate vérifié              ✅
tâches aval bloquées en upstream_failed                 ✅
replay de février réalisé                                ✅
idempotence de février démontrée                        ✅
absence de doublons contrôlée                            ✅
trois runs janvier / février / mars en success           ✅
FCT_TRIPS = 10 382 378                                  ✅
```

---

# Bilan du Bloc 6 ✅

Le Jour 4 est entièrement validé.

Le pipeline Airflow orchestre désormais le flux complet :

```text
RAW
 ↓
contrôle RAW
 ↓
STAGING
 ↓
INTERMEDIATE
 ↓
contrôle du taux de rejet
 ↓
MARTS.FCT_TRIPS
 ↓
contrôle des doublons
 ↓
marts analytiques
```

Les résultats finaux sont reproductibles et les trois mois attendus ont été traités avec succès.

---

# Architecture finale du Jour 4

```text
                              NYC Open Data
                                   │
                                   ▼
                          RAW.YELLOW_TRIPDATA
                                   │
                                   ▼
                       check_raw_month_loaded
                                   │
                                   ▼
                          create_core_tables
                                   │
             ┌─────────────────────┼──────────────────────┐
             │                     │                      │
             ▼                     ▼                      ▼
      STG yellow trips       STG taxi zones           codes TLC
             │                     │                      │
             ▼                     ▼                      ├──→ DIM_VENDOR
    INT_TRIPS__FLAGGED          DIM_ZONE                  ├──→ DIM_PAYMENT_TYPE
             │                                            └──→ DIM_RATE_CODE
             ▼
    check_rejection_rate
          ┌──┴───────────────┐
          │                  │
          ▼                  ▼
 INT_TRIPS__ENRICHED    MART_DATA_QUALITY
          │
          ▼
      FCT_TRIPS
          │
          ▼
 check_trips_no_duplicates
          │
          ├───────────────→ MART_DAILY_REVENUE
          │
          └───────────────→ MART_ZONE_HOURLY_DEMAND

      DIM_DATE
         ▲
         │
 paramètres du DAG
```

Les quality gates sont placés au plus près des données qu'ils contrôlent et bloquent uniquement les branches qui en dépendent.

---

# État final du Jour 4

```text
Bloc 1 — Analyse du SQL et dépendances                 ✅ TERMINÉ
Bloc 2 — Orchestration SQL dans Airflow                ✅ TERMINÉ
Bloc 3 — Contrôles qualité                             ✅ TERMINÉ
Bloc 4 — Test d'échec                                  ✅ TERMINÉ
Bloc 5 — Replay / idempotence                          ✅ TERMINÉ
Bloc 6 — Validation finale                             ✅ TERMINÉ
```

Résultats de référence :

```text
RAW janvier  = 3 475 226 lignes
RAW février  = 3 577 543 lignes
RAW mars     = 4 145 257 lignes

FCT janvier  = 3 251 337 trajets valides
FCT février  = 3 305 246 trajets valides
FCT mars     = 3 825 795 trajets valides

FCT total    = 10 382 378 trajets valides
```

Les trois DagRuns sont en `success` et le replay de février conserve exactement les mêmes volumes.

```text
Jour 4 ✅ TERMINÉ
```
