# Compte rendu — Jour 2

```text
1. Comprendre le chargement Stage → RAW             ✅
2. Créer les formats de fichiers                    ✅
3. Créer le stage interne                           ✅
4. Créer les deux tables RAW                        ✅
5. Charger janvier et vérifier l'idempotence        ✅
6. Écrire le script Python paramétré par mois       ✅
7. Charger les 265 zones                            ✅
```

## Objectif du jour

Le Jour 2 est consacré au chargement des fichiers source dans la couche `RAW` de Snowflake.

Les éléments suivants ont été mis en place :

- les formats de fichiers Parquet et CSV ;
- un stage interne Snowflake ;
- les deux tables RAW imposées par le contrat ;
- le chargement manuel de janvier 2025 ;
- la vérification des colonnes techniques ;
- la vérification de l'idempotence de `COPY INTO` ;
- un script Python paramétré par mois ;
- l'exécution du script depuis Docker avec `uv` ;
- le téléchargement automatique des fichiers NYC ;
- le `PUT` et le `COPY INTO` depuis Python ;
- la vérification de l'idempotence du script complet ;
- le téléchargement et le chargement des 265 zones.

Les principaux fichiers créés ou complétés sont :

```text
snowflake/02_raw.sql
ingestion/load_month.py
ingestion/load_zones.py
ingestion/requirements.txt
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

L'idempotence est une propriété de conception. Snowflake fournit des briques permettant de l'implémenter, par exemple :

```text
OVERWRITE = FALSE
COPY INTO sans FORCE
historique des fichiers chargés
```

### Reproductibilité

La reproductibilité consiste à pouvoir reconstruire plus tard le même résultat à partir :

- des mêmes données source ;
- du même code ;
- des mêmes paramètres ;
- des mêmes dépendances ;
- du même environnement.

Un même nom de fichier ne suffit pas forcément : un fournisseur peut republier un fichier sous le même nom avec un contenu différent. Un hash comme SHA-256 permet de distinguer ces versions.

### Traçabilité

La traçabilité permet de répondre aux questions :

```text
Quoi ?
Quand ?
Par qui ?
Avec quelles données ?
Avec quel code ?
Avec quel résultat ?
```

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

Les montants et mesures utilisent notamment `FLOAT`.

La colonne `cbd_congestion_fee` est présente dans le contrat RAW même si elle n'existe pas dans le fichier de janvier analysé ; elle reste donc `NULL` lorsque la source ne la fournit pas.

### `TAXI_ZONE_LOOKUP`

La table contient :

```text
locationid
borough
zone
service_zone
_source_file
_loaded_at
```

Elle reçoit le référentiel officiel des 265 zones.

---

## 6. Envoi du fichier de janvier dans le stage

Le fichier local utilisé pour le premier test manuel est :

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

Résultat pour janvier :

```text
name = nyc_taxi_stage/yellow_tripdata_2025-01.parquet
size = 59158240
```

Le fichier est bien présent à la racine du stage.

---

## 8. Chargement manuel de janvier dans `YELLOW_TRIPDATA`

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

Résultat pour janvier :

```text
_source_file    = yellow_tripdata_2025-01.parquet
row_count       = 3 475 226
first_loaded_at = 2026-10-06 02:08:01.658
last_loaded_at  = 2026-10-06 02:08:01.658
```

Les colonnes techniques sont correctement alimentées.

---

## 10. Vérification de l'idempotence de janvier

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

## 11. Création du script Python paramétré par mois

Le script suivant a été créé :

```text
ingestion/load_month.py
```

Il reçoit un mois au format :

```text
YYYY-MM
```

Exemple :

```bash
python3 ingestion/load_month.py 2025-01
```

Le format est validé avant exécution.

Exemple valide :

```text
2025-01
→ accepté
```

Exemple invalide :

```text
2025-13
→ ValueError
```

Le script construit automatiquement :

```text
yellow_tripdata_2025-02.parquet
```

et l'URL correspondante :

```text
https://d37ci6vzurychx.cloudfront.net/trip-data/yellow_tripdata_2025-02.parquet
```

---

## 12. Téléchargement automatique depuis NYC

Le script télécharge le Parquet avec `requests` en streaming par morceaux afin de ne pas charger le fichier complet en mémoire.

Le fichier de février a été téléchargé dans :

```text
parquet/yellow_tripdata_2025-02.parquet
```

Résultat :

```text
-rw-r--r-- 1 utilisateur utilisateur 58M oct. 6 16:03 parquet/yellow_tripdata_2025-02.parquet
```

Le téléchargement est exécuté dans Docker avec l'UID/GID de l'utilisateur Ubuntu afin que les fichiers créés n'appartiennent pas à `root`.

---

## 13. Gestion des dépendances avec `uv`

Les dépendances du script sont déclarées dans :

```text
ingestion/requirements.txt
```

Contenu :

```text
requests
snowflake-connector-python
cryptography
```

Le script est exécuté dans un conteneur `uv` :

```bash
docker run --rm \
  --user "$(id -u):$(id -g)" \
  -e UV_CACHE_DIR=/tmp/uv-cache \
  -v "$(pwd):/app" \
  -w /app \
  ghcr.io/astral-sh/uv:python3.12-bookworm-slim \
  uv run \
    --with-requirements ingestion/requirements.txt \
    python ingestion/load_month.py 2025-02
```

`UV_CACHE_DIR=/tmp/uv-cache` évite les problèmes de permissions lorsque le conteneur est exécuté avec l'UID de l'utilisateur local.

---

## 14. Connexion Snowflake depuis le script

La connexion Snowflake est intégrée directement dans `load_month.py`.

La clé privée est montée en lecture seule dans Docker :

```text
/run/secrets/rsa_key.p8
```

Les paramètres Snowflake sont transmis au conteneur via des variables d'environnement.

Test obtenu :

```text
Snowflake connection:
('AIRFLOW_SVC', 'TRANSFORMER', 'NYC_TAXI_WH', 'NYC_TAXI', 'RAW')
```

Cela confirme que le script utilise bien :

```text
AIRFLOW_SVC
    ↓
TRANSFORMER
    ↓
NYC_TAXI_WH
    ↓
NYC_TAXI.RAW
```

---

## 15. `PUT` et `COPY INTO` depuis le script Python

Le script `load_month.py` réalise maintenant le pipeline complet :

```text
mois
 ↓
construction de l'URL
 ↓
téléchargement NYC
 ↓
fichier Parquet local
 ↓
PUT
 ↓
NYC_TAXI_STAGE
 ↓
COPY INTO
 ↓
RAW.YELLOW_TRIPDATA
```

Premier chargement complet de février :

```text
PUT result:
SKIPPED
```

Le `PUT` est `SKIPPED` car le fichier avait déjà été déposé dans le stage lors du test précédent.

Le `COPY INTO` a ensuite chargé février :

```text
status       = LOADED
rows_parsed  = 3 577 543
rows_loaded  = 3 577 543
errors_seen  = 0
```

---

## 16. Idempotence du script complet

Le script complet a été rejoué pour février sans modification.

Résultat :

```text
PUT
→ SKIPPED
```

puis :

```text
COPY INTO
→ LOAD_SKIPPED
→ File was loaded before.
```

Contrôle dans Snowflake :

```sql
SELECT
    _source_file,
    COUNT(*) AS row_count
FROM NYC_TAXI.RAW.YELLOW_TRIPDATA
GROUP BY _source_file
ORDER BY _source_file;
```

Résultat :

```text
yellow_tripdata_2025-01.parquet  → 3 475 226
yellow_tripdata_2025-02.parquet  → 3 577 543
```

Le pipeline complet peut donc être rejoué sans doubler les lignes déjà chargées.

---

## 17. Chargement du référentiel des zones

Un second script a été créé :

```text
ingestion/load_zones.py
```

La source utilisée est :

```text
https://d37ci6vzurychx.cloudfront.net/misc/taxi_zone_lookup.csv
```

Le fichier est téléchargé dans :

```text
csv/taxi_zone_lookup.csv
```

Les premières lignes sont :

```csv
"LocationID","Borough","Zone","service_zone"
1,"EWR","Newark Airport","EWR"
2,"Queens","Jamaica Bay","Boro Zone"
3,"Bronx","Allerton/Pelham Gardens","Boro Zone"
4,"Manhattan","Alphabet City","Yellow Zone"
```

Contrôle du nombre de lignes physiques :

```bash
wc -l csv/taxi_zone_lookup.csv
```

Résultat :

```text
266 csv/taxi_zone_lookup.csv
```

Soit :

```text
1 ligne d'en-tête
+ 265 zones
```

---

## 18. `PUT` du fichier des zones

Le script `load_zones.py` télécharge le CSV puis l'envoie dans le stage.

Premier `PUT` :

```text
PUT result:
('taxi_zone_lookup.csv',
 'taxi_zone_lookup.csv',
 12331,
 12336,
 'NONE',
 'NONE',
 'UPLOADED',
 '')
```

Lors de l'exécution suivante :

```text
PUT
→ SKIPPED
```

Le fichier n'est donc pas envoyé une seconde fois.

---

## 19. `COPY INTO TAXI_ZONE_LOOKUP`

Le script charge ensuite les données dans :

```text
NYC_TAXI.RAW.TAXI_ZONE_LOOKUP
```

Résultat :

```text
status       = LOADED
rows_parsed  = 265
rows_loaded  = 265
errors_seen  = 0
```

---

## 20. Vérification finale des zones

Requête :

```sql
SELECT
    COUNT(*) AS row_count,
    COUNT(DISTINCT locationid) AS distinct_location_ids,
    MIN(_loaded_at) AS first_loaded_at,
    MAX(_loaded_at) AS last_loaded_at
FROM NYC_TAXI.RAW.TAXI_ZONE_LOOKUP;
```

Résultat :

```text
row_count             = 265
distinct_location_ids = 265
first_loaded_at       = 2026-10-06 07:24:39.405
last_loaded_at        = 2026-10-06 07:24:39.405
```

Vérification de la provenance :

```sql
SELECT
    _source_file,
    COUNT(*) AS row_count
FROM NYC_TAXI.RAW.TAXI_ZONE_LOOKUP
GROUP BY _source_file;
```

Résultat :

```text
_source_file = taxi_zone_lookup.csv
row_count    = 265
```

Les 265 zones sont présentes, les identifiants sont uniques dans le jeu de données chargé et les colonnes techniques sont correctement alimentées.

---

## État final du Jour 2

```text
Formats de fichiers                              ✅
Stage interne                                    ✅
Tables RAW                                       ✅
PUT janvier                                      ✅
COPY INTO janvier                                ✅
Colonnes techniques                              ✅
Idempotence de janvier                           ✅
Script Python paramétré par mois                 ✅
Téléchargement automatique NYC                   ✅
Dépendances versionnées                          ✅
Connexion Snowflake depuis Docker                ✅
PUT depuis Python                                ✅
COPY INTO depuis Python                          ✅
Chargement de février                            ✅
Idempotence du script complet                    ✅
Téléchargement du référentiel des zones          ✅
Chargement des 265 zones                         ✅
Contrôles finaux RAW                             ✅
```

## Résultat du Jour 2

La couche RAW contient maintenant :

```text
YELLOW_TRIPDATA
├── janvier 2025 : 3 475 226 lignes
└── février 2025 : 3 577 543 lignes

TAXI_ZONE_LOOKUP
└── 265 zones
```

Le pipeline d'ingestion mensuel est paramétré par mois, conteneurisé avec Docker, utilise `uv` pour ses dépendances, s'authentifie à Snowflake avec `AIRFLOW_SVC` et peut être rejoué sans dupliquer un fichier déjà chargé.

Le Jour 2 est terminé.
