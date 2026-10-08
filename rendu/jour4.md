# Compte rendu — Jour 4

# Transformer et contrôler les données avec Airflow

## État d'avancement

```text
Bloc 1 — Lire et comprendre les fichiers SQL fournis           ✅ TERMINÉ
Bloc 2 — Ajouter les transformations SQL au DAG                ✅ TERMINÉ
Bloc 3 — Ajouter les contrôles de qualité                       ⏳ À FAIRE
Bloc 4 — Provoquer volontairement l'échec d'un contrôle        ⏳ À FAIRE
Bloc 5 — Rejouer février et vérifier l'idempotence              ⏳ À FAIRE
Bloc 6 — Validation finale du Jour 4                            ⏳ À FAIRE
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

# Bloc 3 — Ajouter les contrôles de qualité ⏳ À FAIRE

Le brief demande de brancher :

```text
controles/raw_mois_charge.sql
```

puis d'écrire au moins deux contrôles supplémentaires.

Contrôles attendus :

```text
[ ] mois RAW chargé
[ ] absence de trajets en double
[ ] seuil maximum de trajets rejetés
```

Ils devront utiliser :

```text
SQLCheckOperator
```

avec :

```text
retries=0
```

### État

```text
⏳ À FAIRE
```

---

# Bloc 4 — Tester volontairement un échec ⏳ À FAIRE

Principe attendu :

```text
durcir temporairement un seuil
        ↓
relancer un run
        ↓
contrôle en échec
        ↓
vérifier que les tâches suivantes ne s'exécutent pas
        ↓
restaurer le seuil normal
```

Objectif :

```text
prouver qu'Airflow bloque le pipeline lorsque la qualité des données est insuffisante
```

### État

```text
⏳ À FAIRE
```

---

# Bloc 5 — Rejouer février et vérifier l'idempotence ⏳ À FAIRE

Les runs du Jour 3 sont déjà terminés.

Les nouvelles tâches devront être rejouées avec `Clear`.

Contrôles attendus :

```text
[ ] noter le nombre de lignes avant replay
[ ] rejouer février
[ ] vérifier le nombre de lignes après replay
[ ] confirmer l'absence de doublon
```

Le mécanisme repose sur :

```text
DELETE du mois
+
INSERT du mois
```

### État

```text
⏳ À FAIRE
```

---

# Bloc 6 — Validation finale du Jour 4 ⏳ À FAIRE

## Résultat attendu

Trois exécutions réussies :

```text
2025-01 ✅
2025-02 ✅
2025-03 ✅
```

Volume attendu :

```text
NYC_TAXI.MARTS.FCT_TRIPS
=
10 382 378 trajets valides
```

Checklist :

```text
[ ] trois runs Airflow en success
[ ] FCT_TRIPS = 10 382 378 lignes
[ ] dimensions créées
[ ] marts créés
[ ] MART_DATA_QUALITY alimenté
[ ] contrôles Airflow passants
[ ] replay de février idempotent
```

### État

```text
⏳ À FAIRE
```

---

# Architecture cible du Jour 4

```text
                           NYC Open Data
                                │
                                ▼
                         RAW.YELLOW_TRIPDATA
                                │
                                ▼
                         contrôle RAW
                                │
                                ▼
                             STAGING
                   ┌────────────┼────────────┐
                   │            │            │
                   ▼            ▼            ▼
             yellow trips     zones      codes TLC
                   │            │            │
                   ▼            │            ├──→ DIM_VENDOR
          INT_TRIPS__FLAGGED    │            ├──→ DIM_PAYMENT_TYPE
                   │            │            └──→ DIM_RATE_CODE
          ┌────────┴───────┐    │
          │                │    ▼
          ▼                │  DIM_ZONE
 INT_TRIPS__ENRICHED       │
          │                ▼
          ▼          MART_DATA_QUALITY
      FCT_TRIPS
          │
          ├────────→ MART_DAILY_REVENUE
          │
          └────────→ MART_ZONE_HOURLY_DEMAND

              DIM_DATE
                 ▲
                 │
         paramètres du DAG
```

---

# État actuel du Jour 4

```text
Bloc 1 — Analyse du SQL et dépendances                 ✅
Bloc 2 — Orchestration SQL dans Airflow                ✅
Bloc 3 — Contrôles qualité                             ⏳
Bloc 4 — Test d'échec                                  ⏳
Bloc 5 — Replay / idempotence                          ⏳
Bloc 6 — Validation finale                             ⏳
```

Le Bloc 1 est terminé.

La reprise pourra commencer directement par :

```text
Bloc 2
→ préparer le DAG pour exécuter les fichiers SQL
→ template_searchpath
```
