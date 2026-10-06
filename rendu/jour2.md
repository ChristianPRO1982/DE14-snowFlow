# Compte rendu — Jour 2

```text
1. Comprendre le chargement Stage → RAW             ✅
2. Créer les formats de fichiers                    ✅
3. Créer le stage interne                           ✅
4. Créer les deux tables RAW                        ✅
5. Charger janvier et vérifier l'idempotence        ✅
6. Écrire le script Python paramétré par mois       ⏸️ Non commencé
7. Charger les 265 zones                            ⏳ À faire
```

## Objectif du jour

Le Jour 2 est consacré au chargement des fichiers source dans la couche `RAW` de Snowflake.

À ce stade, les éléments suivants ont été mis en place :

- les formats de fichiers Parquet et CSV ;
- un stage interne Snowflake ;
- les deux tables RAW imposées par le contrat ;
- le chargement du fichier de janvier 2025 ;
- la vérification du bon remplissage des colonnes techniques ;
- la vérification de l'idempotence du `COPY INTO`.

Le script SQL utilisé est :

```text
snowflake/02_raw.sql
```

---

## 1. Compréhension du mécanisme Stage → RAW

Le chargement suit cette chaîne :

```text
fichier local
    │
    │ PUT
    ▼
stage interne Snowflake
    │
    │ COPY INTO
    ▼
table RAW
```

### `PUT`

`PUT` déplace physiquement un fichier depuis la machine qui exécute la commande vers un stage Snowflake.

Il doit donc être exécuté depuis un environnement ayant accès au fichier local, par exemple Python dans Docker.

### `COPY INTO`

`COPY INTO` ne copie pas le fichier lui-même. Snowflake lit son contenu, interprète les colonnes à l'aide d'un `FILE FORMAT`, insère les données dans une table et peut ajouter des métadonnées techniques lors du chargement.

Le fichier reste donc un fichier dans le stage, tandis que la table RAW contient les données structurées qui en ont été extraites.

---

## 2. Idempotence, reproductibilité et traçabilité

### Idempotence

Une opération idempotente peut être rejouée sans modifier davantage l'état final.

```text
1er chargement
→ 3 475 226 lignes

2e chargement identique
→ toujours 3 475 226 lignes
```

L'idempotence est une propriété de conception. Snowflake fournit des briques permettant de l'implémenter, par exemple `OVERWRITE = FALSE`, `COPY INTO` sans `FORCE` et l'historique des fichiers chargés.

### Reproductibilité

La reproductibilité consiste à pouvoir reconstruire plus tard le même résultat à partir des mêmes données source, du même code, des mêmes paramètres, des mêmes dépendances et du même environnement.

Un même nom de fichier ne suffit pas forcément : un fournisseur peut republier un fichier sous le même nom avec un contenu différent. Un hash comme SHA-256 permet de distinguer ces versions.

### Traçabilité

La traçabilité permet de répondre aux questions : quoi, quand, par qui, avec quelles données, avec quel code et avec quel résultat ?

Les colonnes techniques, les logs, les historiques de chargement et les tables d'audit y contribuent.

---

## 3. Création des formats de fichiers

Deux formats ont été créés dans `NYC_TAXI.RAW`.

### Parquet

```sql
CREATE OR REPLACE FILE FORMAT PARQUET_FF
  TYPE = PARQUET;
```

Résultat :

```text
name   = PARQUET_FF
type   = PARQUET
owner  = TRANSFORMER
schema = NYC_TAXI.RAW
```

### CSV

```sql
CREATE OR REPLACE FILE FORMAT CSV_FF
  TYPE = CSV
  PARSE_HEADER = TRUE
  FIELD_OPTIONALLY_ENCLOSED_BY = '"'
  ERROR_ON_COLUMN_COUNT_MISMATCH = FALSE;
```

Résultat :

```text
name   = CSV_FF
type   = CSV
owner  = TRANSFORMER
schema = NYC_TAXI.RAW
```

---

## 4. Création du stage interne

Le stage interne créé est :

```text
NYC_TAXI.RAW.NYC_TAXI_STAGE
```

Commande :

```sql
CREATE STAGE IF NOT EXISTS NYC_TAXI_STAGE
  COMMENT = 'Internal stage for NYC Taxi source files';
```

Résultat :

```text
name  = NYC_TAXI_STAGE
type  = INTERNAL
owner = TRANSFORMER
```

Le stage sert de zone de dépôt des fichiers avant leur chargement dans les tables RAW.

---

## 5. Création des tables RAW

Deux tables ont été créées dans `NYC_TAXI.RAW` :

```text
YELLOW_TRIPDATA
TAXI_ZONE_LOOKUP
```

Les deux appartiennent à `TRANSFORMER`.

### `YELLOW_TRIPDATA`

La table contient les colonnes métier du fichier Yellow Taxi ainsi que deux colonnes techniques :

```text
_source_file
_loaded_at
```

Les montants et mesures utilisent notamment `FLOAT`. La colonne `cbd_congestion_fee` est présente dans le contrat RAW même si elle n'existe pas dans le fichier de janvier analysé ; elle reste donc `NULL` lorsque la source ne la fournit pas.

### `TAXI_ZONE_LOOKUP`

La table est créée et prête à recevoir les 265 zones. Elle est encore vide à ce stade.

---

## 6. Envoi du fichier de janvier dans le stage

Le fichier local est :

```text
./parquet/yellow_tripdata_2025-01.parquet
```

Vérification locale :

```bash
ls -lh ./parquet/yellow_tripdata_2025-01.parquet
```

Résultat :

```text
-rw-rw-r-- 1 utilisateur utilisateur 57M oct. 5 12:02 ./parquet/yellow_tripdata_2025-01.parquet
```

Le fichier a ensuite été envoyé dans Snowflake depuis un conteneur Docker :

```bash
docker run --rm -i \
  -v "$HOME/.ssh/snowflake/rsa_key.p8:/run/secrets/rsa_key.p8:ro" \
  -v "$(pwd)/parquet/yellow_tripdata_2025-01.parquet:/data/yellow_tripdata_2025-01.parquet:ro" \
  ghcr.io/astral-sh/uv:python3.12-bookworm-slim \
  uv run \
    --with snowflake-connector-python \
    --with cryptography \
    python - <<'PY'
import snowflake.connector
from cryptography.hazmat.primitives import serialization

with open("/run/secrets/rsa_key.p8", "rb") as key_file:
    private_key = serialization.load_pem_private_key(
        key_file.read(),
        password=None,
    )

conn = snowflake.connector.connect(
    account="KWJSUAI-TM59629",
    user="AIRFLOW_SVC",
    private_key=private_key,
    role="TRANSFORMER",
    warehouse="NYC_TAXI_WH",
    database="NYC_TAXI",
    schema="RAW",
)

with conn.cursor() as cur:
    cur.execute(
        """
        PUT file:///data/yellow_tripdata_2025-01.parquet
        @NYC_TAXI_STAGE
        AUTO_COMPRESS=FALSE
        OVERWRITE=FALSE
        """
    )

    for row in cur.fetchall():
        print(row)

conn.close()
PY
```

Résultat :

```text
('yellow_tripdata_2025-01.parquet',
 'yellow_tripdata_2025-01.parquet',
 59158238,
 59158240,
 'PARQUET',
 'PARQUET',
 'UPLOADED',
 '')
```

`AUTO_COMPRESS = FALSE` conserve le nom exact du Parquet et `OVERWRITE = FALSE` évite d'écraser automatiquement un fichier déjà présent.

---

## 7. Vérification du stage

Requête :

```sql
LIST @NYC_TAXI_STAGE;
```

Résultat :

```text
name = nyc_taxi_stage/yellow_tripdata_2025-01.parquet
size = 59158240
```

Le fichier est bien présent à la racine du stage.

---

## 8. Chargement du fichier dans `YELLOW_TRIPDATA`

Commande exécutée :

```sql
COPY INTO YELLOW_TRIPDATA
FROM @NYC_TAXI_STAGE
FILES = ('yellow_tripdata_2025-01.parquet')
FILE_FORMAT = (FORMAT_NAME = PARQUET_FF)
MATCH_BY_COLUMN_NAME = CASE_INSENSITIVE
INCLUDE_METADATA = (
    _source_file = METADATA$FILENAME,
    _loaded_at = METADATA$START_SCAN_TIME
)
ON_ERROR = ABORT_STATEMENT;
```

Résultat :

```text
status       = LOADED
rows_parsed  = 3 475 226
rows_loaded  = 3 475 226
errors_seen  = 0
```

Le nombre de lignes correspond exactement au nombre de trajets détecté lors de l'audit du fichier de janvier.

---

## 9. Vérification des colonnes techniques

Requête :

```sql
SELECT
    _source_file,
    COUNT(*) AS row_count,
    MIN(_loaded_at) AS first_loaded_at,
    MAX(_loaded_at) AS last_loaded_at
FROM NYC_TAXI.RAW.YELLOW_TRIPDATA
GROUP BY _source_file;
```

Résultat :

```text
_source_file    = yellow_tripdata_2025-01.parquet
row_count       = 3 475 226
first_loaded_at = 2026-10-06 02:08:01.658
last_loaded_at  = 2026-10-06 02:08:01.658
```

Les colonnes techniques sont correctement alimentées.

---

## 10. Vérification de l'idempotence

Le même `COPY INTO` a été rejoué sans modification.

Résultat :

```text
status       = LOAD_SKIPPED
rows_parsed  = 0
rows_loaded  = 0
first_error  = File was loaded before.
```

Contrôle du nombre de lignes :

```sql
SELECT COUNT(*)
FROM NYC_TAXI.RAW.YELLOW_TRIPDATA;
```

Résultat :

```text
3 475 226
```

Le second chargement n'a donc créé aucun doublon.

---

## État actuel du Jour 2

```text
Formats de fichiers                  ✅
Stage interne                        ✅
Tables RAW                           ✅
PUT janvier                          ✅
COPY INTO janvier                    ✅
Colonnes techniques                  ✅
Idempotence du chargement            ✅
Script Python paramétré par mois     ⏸️ Non commencé
Chargement des 265 zones             ⏳ À faire
```

## Prochaine étape

La prochaine étape sera reprise depuis le début :

```text
Étape 6 — écrire le script Python paramétré par mois
```

Aucun code ni fichier de cette étape n'a encore été créé.
