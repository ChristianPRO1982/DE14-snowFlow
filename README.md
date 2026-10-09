# DE14 — SnowFlow + Airflow

Pipeline de données **NYC Yellow Taxi** construit avec **Snowflake** et **Apache Airflow**.

Ce dépôt répond au brief Simplon :

> Pipeline médaillon NYC Yellow Taxi : Snowflake + Airflow

Le projet charge les données publiques de la NYC Taxi & Limousine Commission (TLC), applique des transformations SQL dans Snowflake, contrôle la qualité des données et produit des marts destinés à l'analyse métier.

---

## Objectifs

Le pipeline doit être :

- automatisé ;
- mensuel ;
- rejouable ;
- idempotent ;
- sécurisé par clé RSA ;
- orchestré avec Airflow ;
- contrôlé par des quality gates ;
- exploitable pour répondre à une question métier.

La période étudiée est :

```text
Janvier 2025
Février 2025
Mars 2025
```

---

# Architecture

```text
NYC TLC
  |
  | Parquet mensuel Yellow Taxi
  v
Airflow
  |
  | téléchargement
  | PUT
  v
Snowflake internal stage
  |
  | COPY INTO
  v
RAW
  |
  v
STAGING
  |
  v
INTERMEDIATE
  |
  +---- contrôles qualité
  |
  v
MARTS
  |
  +---- FCT_TRIPS
  +---- dimensions
  +---- MART_DATA_QUALITY
  +---- MART_DAILY_REVENUE
  +---- MART_ZONE_HOURLY_DEMAND
```

Le mois traité par Airflow est déterminé à partir de la **logical date** de l'exécution et non à partir de la date du jour.

---

# Stack technique

- Snowflake
- Apache Airflow 3
- Astronomer Astro CLI
- Python
- SQL
- Docker
- `apache-airflow-providers-snowflake`
- `snowflake-connector-python`
- authentification RSA par clé privée

---

# Structure du dépôt

```text
.
├── airflow/
│   ├── dags/
│   │   └── nyc_taxi_monthly.py
│   ├── include/
│   │   └── sql/
│   ├── tests/
│   ├── .env.example
│   └── requirements.txt
│
├── docs/
│   ├── fiche_trajets.md
│   └── REPONSE.md
│
├── ingestion/
│   ├── load_month.py
│   ├── load_zones.py
│   └── requirements.txt
│
├── snowflake/
│   ├── 01_infrastructure.sql
│   └── 02_raw.sql
│
├── parquet/
│   ├── audit_parquet.sh
│   ├── audit_results.md
│   └── explore.sql
│
├── rendu/
│   ├── jour1.md
│   ├── jour2.md
│   ├── jour3.md
│   ├── jour4.md
│   └── jour5.md
│
└── README.md
```

Les fichiers source téléchargés (`*.parquet`, `*.csv`) ne sont pas versionnés.

---

# Prérequis

Pour reproduire le projet :

- un compte Snowflake ;
- Python ;
- Docker ;
- Astro CLI ;
- Git ;
- OpenSSL ;
- une paire de clés RSA pour l'utilisateur de service Snowflake.

---

# 1. Cloner le dépôt

```bash
git clone git@github.com:ChristianPRO1982/DE14-snowFlow.git
cd DE14-snowFlow
```

---

# 2. Créer l'infrastructure Snowflake

Exécuter dans Snowflake :

```text
snowflake/01_infrastructure.sql
```

Ce script crée notamment :

```text
ROLE       TRANSFORMER
WAREHOUSE  NYC_TAXI_WH
DATABASE   NYC_TAXI

SCHEMAS
├── RAW
├── STAGING
├── INTERMEDIATE
└── MARTS

USER
└── AIRFLOW_SVC
```

Le warehouse est configuré avec :

```text
SIZE         = X-Small
AUTO_SUSPEND = 60 secondes
AUTO_RESUME  = TRUE
```

Le rôle `TRANSFORMER` reçoit uniquement les droits nécessaires au pipeline dans le périmètre `NYC_TAXI`.

---

# 3. Créer la couche RAW

Exécuter :

```text
snowflake/02_raw.sql
```

Ce script crée :

```text
PARQUET_FF
CSV_FF
NYC_TAXI_STAGE
YELLOW_TRIPDATA
TAXI_ZONE_LOOKUP
```

Le format Parquet utilise :

```sql
USE_LOGICAL_TYPE = TRUE
```

afin que les timestamps logiques du fichier Parquet soient correctement interprétés par Snowflake.

---

# 4. Authentification Snowflake

Le pipeline utilise l'utilisateur de service :

```text
AIRFLOW_SVC
```

avec le rôle :

```text
TRANSFORMER
```

L'authentification repose sur une paire de clés RSA.

La clé privée :

- n'est pas stockée dans Git ;
- n'est pas écrite dans le DAG ;
- est fournie à Airflow via son environnement local.

Le fichier :

```text
airflow/.env.example
```

documente la configuration attendue.

Créer le fichier local :

```bash
cd airflow
cp .env.example .env
```

Puis renseigner la connexion Snowflake dans `.env`.

Le fichier `.env` est ignoré par Git.

---

# 5. Chargement manuel Python

Les scripts d'ingestion sont conservés pour permettre un chargement ou un test indépendant d'Airflow.

Créer un environnement Python :

```bash
uv venv
source .venv/bin/activate
uv pip install -r ingestion/requirements.txt
```

Variables nécessaires :

```text
SNOWFLAKE_ACCOUNT
SNOWFLAKE_USER
SNOWFLAKE_ROLE
SNOWFLAKE_WAREHOUSE
SNOWFLAKE_DATABASE
SNOWFLAKE_SCHEMA
SNOWFLAKE_PRIVATE_KEY_PATH
```

Exemple de chargement mensuel :

```bash
python ingestion/load_month.py 2025-01
```

Chargement du référentiel des zones :

```bash
python ingestion/load_zones.py
```

Le chargement est conçu pour être rejouable.

---

# 6. Lancer Airflow

Depuis le dossier `airflow/` :

```bash
cd airflow
astro dev start
```

L'interface Airflow est ensuite accessible localement.

Le DAG principal est :

```text
nyc_taxi_monthly
```

Il est configuré avec :

```text
schedule        = @monthly
start_date      = 2025-01-01
end_date        = 2025-03-01
catchup         = True
max_active_runs = 1
```

Airflow crée ainsi les exécutions correspondant aux trois mois étudiés.

---

# Pipeline Airflow

Le pipeline suit l'ordre logique suivant :

```text
Téléchargement du fichier TLC
        |
        v
PUT vers le stage Snowflake
        |
        v
COPY INTO RAW
        |
        v
Contrôle RAW
        |
        v
STAGING
        |
        v
INTERMEDIATE
        |
        v
Contrôle du taux de rejet
        |
        v
MARTS
        |
        v
Contrôle des doublons
        |
        v
Marts analytiques
```

Les transformations SQL sont stockées dans :

```text
airflow/include/sql/
```

Le DAG orchestre leur exécution sans dupliquer la logique SQL dans le code Python.

---

# Contrôles qualité

Le pipeline contient plusieurs quality gates.

## RAW chargé

Le pipeline vérifie que le mois attendu a effectivement été chargé dans la couche RAW.

## Taux de rejet

Le seuil maximal est :

```text
10 %
```

Les taux observés sont environ :

```text
Janvier 2025  : 6,443 %
Février 2025  : 7,611 %
Mars 2025     : 7,708 %
```

## Absence de doublons

Le contrôle compare :

```sql
COUNT(*)
```

avec :

```sql
COUNT(DISTINCT trip_sk)
```

dans `MARTS.FCT_TRIPS`.

Une erreur de contrôle bloque les tâches dépendantes.

---

# Idempotence

Le pipeline peut être rejoué pour un mois déjà traité sans créer de doublons.

Le replay de février 2025 a été testé.

Avant et après replay :

```text
INT_TRIPS__FLAGGED  = 3 577 543
INT_TRIPS__ENRICHED = 3 305 246
FCT_TRIPS            = 3 305 246
```

Les volumes restent identiques.

---

# Volumes traités

## RAW

```text
Janvier 2025  : 3 475 226 lignes
Février 2025  : 3 577 543 lignes
Mars 2025     : 4 145 257 lignes
```

Total RAW :

```text
11 198 026 lignes
```

## MARTS.FCT_TRIPS

Après application des règles qualité :

```text
Janvier 2025  : 3 251 337
Février 2025  : 3 305 246
Mars 2025     : 3 825 795
```

Total :

```text
10 382 378 trajets valides
```

---

# Data Quality

Les anomalies sont détectées dans :

```text
NYC_TAXI.INTERMEDIATE.INT_TRIPS__FLAGGED
```

et agrégées dans :

```text
NYC_TAXI.MARTS.MART_DATA_QUALITY
```

Une comparaison directe a confirmé :

```text
INT_TRIPS__FLAGGED = MART_DATA_QUALITY
DIFFERENCE         = 0
```

pour chaque mois et chaque motif de rejet.

Les principales causes d'exclusion sont :

```text
amount_non_positive
distance_out_of_range
```

---

# Sécurité et moindre privilège

Airflow utilise :

```text
USER : AIRFLOW_SVC
ROLE : TRANSFORMER
```

Le rôle peut :

- utiliser `NYC_TAXI_WH` ;
- accéder à `NYC_TAXI` ;
- créer et manipuler les objets nécessaires au pipeline.

Un test hors périmètre a été effectué :

```sql
CREATE DATABASE SHOULD_FAIL;
```

Résultat :

```text
Insufficient privileges
```

Le rôle `TRANSFORMER` ne possède donc pas de privilège `CREATE DATABASE` au niveau du compte.

---

# Consommation Snowflake

Le warehouse utilisé est :

```text
NYC_TAXI_WH
```

Configuration :

```text
Size         : X-Small
Auto-suspend : 60 secondes
Auto-resume  : true
```

Consommation mesurée lors de la validation du projet :

```text
Crédits totaux          : 0,8312
Compute                 : 0,8130
Cloud services          : 0,0182
```

Cette valeur évoluera naturellement si de nouvelles requêtes ou exécutions sont lancées.

---

# Réponse métier

La réponse complète est disponible dans :

```text
docs/REPONSE.md
```

L'analyse s'appuie notamment sur :

```text
MART_ZONE_HOURLY_DEMAND
MART_DAILY_REVENUE
```

Parmi les résultats observés :

- East Village concentre une forte demande les nuits de week-end ;
- Midtown Center présente une forte demande en semaine entre 17 h et 21 h ;
- la carte bancaire est le principal mode de paiement observé.

La période étudiée étant limitée à trois mois, ces résultats ne permettent pas de conclure à une saisonnalité annuelle.

---

# Comptes rendus

Le développement du projet est documenté jour par jour :

| Jour | Document | Contenu |
|---|---|---|
| Jour 1 | [rendu/jour1.md](rendu/jour1.md) | Source, architecture, infrastructure Snowflake et sécurité |
| Jour 2 | [rendu/jour2.md](rendu/jour2.md) | RAW, stage, formats de fichiers et chargement |
| Jour 3 | [rendu/jour3.md](rendu/jour3.md) | Airflow, Astro et connexion Snowflake |
| Jour 4 | [rendu/jour4.md](rendu/jour4.md) | Transformations, DAG, quality gates et idempotence |
| Jour 5 | [rendu/jour5.md](rendu/jour5.md) | Réponse métier, qualité, crédits, sécurité et finalisation |

La fiche descriptive de la source est disponible dans :

```text
docs/fiche_trajets.md
```

---

# Sources de données

NYC Taxi & Limousine Commission — TLC Trip Record Data.

Les fichiers Yellow Taxi mensuels sont téléchargés automatiquement par le pipeline depuis la source publique TLC.

Les fichiers de données téléchargés localement ne sont pas stockés dans le dépôt Git.

---

# Auteur

Projet réalisé individuellement par :

[ChristianPRO1982](https://github.com/ChristianPRO1982)

dans le cadre de la formation Data Engineer Simplon.
