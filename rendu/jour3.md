# Compte rendu — Jour 3

```text
1. Initialiser le projet Astro / Airflow                 ✅
2. Configurer la connexion Snowflake                     ✅
3. Tester AIRFLOW_SVC depuis un DAG                      ✅
4. Comprendre la date logique                            ✅
5. Construire le DAG mensuel                             ✅
6. Vérifier l'existence du fichier                       ✅
7. Télécharger le fichier                                ✅
8. Envoyer le fichier sur le stage                       ✅
9. Copier le fichier dans RAW                            ✅
10. Activer le catchup Jan / Fév / Mars                  ✅
11. Obtenir trois runs Airflow en succès                 ✅
12. Vérifier les volumes RAW dans Snowflake              ✅
```

## Objectif du jour

Le Jour 3 est consacré à l'automatisation du chargement mensuel avec Airflow 3, lancé localement avec Astro CLI.

L'objectif est de reprendre la logique validée au Jour 2 :

```text
source NYC
   ↓
téléchargement
   ↓
fichier local
   ↓
PUT
   ↓
stage Snowflake
   ↓
COPY INTO
   ↓
RAW.YELLOW_TRIPDATA
```

et de la transformer en pipeline orchestré par Airflow.

À la fin de la journée, trois exécutions historiques doivent être jouées avec succès :

```text
janvier 2025
février 2025
mars 2025
```

Le DAG principal est :

```text
airflow/dags/nyc_taxi_monthly.py
```

Un DAG temporaire de diagnostic a aussi été créé :

```text
airflow/dags/test_snowflake_connection.py
```

---

## 1. Installation d'Astro CLI

Le travail a été repris sur un autre PC Ubuntu, sur lequel la commande `astro` n'était pas encore installée :

```text
zsh: command not found: astro
```

Installation :

```bash
curl -sSL install.astronomer.io | sudo bash -s
```

Vérification :

```bash
astro version
```

Résultat :

```text
Astro CLI Version: 1.46.0
```

Astro CLI est installé sur l'hôte Ubuntu car il sert à piloter les conteneurs Airflow.

---

## 2. Initialisation du projet Astro

Le starter kit contenait déjà un dossier `airflow/`.

Initialisation :

```bash
cd airflow
astro dev init
```

Comme le dossier n'était pas vide, Astro a demandé confirmation :

```text
/home/christianpro1982/Documents/Simplon/DE14-snowFlow/airflow is not an empty directory.
Are you sure you want to initialize a project here? (y/n) y
```

Résultat :

```text
Initialized empty Astro project in ...
```

Après initialisation, le dossier contenait notamment :

```text
.astro/
.dockerignore
.env
.env.example
.gitignore
Dockerfile
README.md
airflow_settings.yaml
dags/
include/
packages.txt
plugins/
requirements.txt
tests/
```

Les fichiers fournis par le starter kit ont bien été conservés.

---

## 3. Dépendances Airflow

Le fichier :

```text
airflow/requirements.txt
```

contient :

```text
apache-airflow-providers-snowflake>=6.0
apache-airflow-providers-common-sql
requests>=2.32
```

Ces dépendances servent à :

- communiquer avec Snowflake ;
- utiliser `SnowflakeHook` ;
- effectuer les requêtes HTTP vers les fichiers NYC.

---

## 4. Nettoyage du DAG d'exemple

Astro avait généré :

```text
dags/exampledag.py
```

Il a été supprimé :

```bash
rm dags/exampledag.py
```

Le dossier `dags/` ne contenait ensuite plus que :

```text
dags/.gitkeep
dags/.airflowignore
```

---

## 5. Création d'une seconde paire de clés Snowflake

Ce second PC ne possédait pas la clé privée du premier poste :

```bash
ls -l ~/.ssh/snowflake/rsa_key.p8
```

Résultat :

```text
Aucun fichier ou répertoire de ce type
```

Une nouvelle paire de clés dédiée à ce poste a donc été créée :

```bash
mkdir -p ~/.ssh/snowflake
```

```bash
openssl genrsa 2048 \
  | openssl pkcs8 -topk8 -inform PEM \
  -out ~/.ssh/snowflake/rsa_key.p8 \
  -nocrypt
```

```bash
openssl rsa \
  -in ~/.ssh/snowflake/rsa_key.p8 \
  -pubout \
  -out ~/.ssh/snowflake/rsa_key.pub
```

Puis :

```bash
chmod 600 ~/.ssh/snowflake/rsa_key.p8
```

Le principe retenu est :

```text
AIRFLOW_SVC
├── RSA_PUBLIC_KEY    → premier PC
└── RSA_PUBLIC_KEY_2  → second PC
```

La seconde clé permet donc d'utiliser le même utilisateur de service depuis deux postes, sans partager la même clé privée.

---

## 6. Incident de sécurité et rotation de clé

Lors d'un test avec :

```bash
astro dev run connections get snowflake_nyc_taxi
```

Airflow a affiché le champ `private_key_content`.

La clé privée étant apparue en clair dans la sortie terminal, elle a été considérée comme exposée.

La seconde clé a donc été immédiatement révoquée dans Snowflake :

```sql
USE ROLE USERADMIN;

ALTER USER AIRFLOW_SVC
UNSET RSA_PUBLIC_KEY_2;
```

La première clé est restée active.

Une nouvelle paire de clés a ensuite été générée et enregistrée.

Empreinte finale de la nouvelle clé du second PC :

```text
SHA256:yBIKj17sF78/ndzDHEVxEmleCoGF+TdU6BrVECpFAW0=
```

Vérification Snowflake :

```text
RSA_PUBLIC_KEY_FP
= SHA256:Z0/C2z+aAOGQVGYrlG0G3l2vvXCEXWt2cKUKmURWW7o=

RSA_PUBLIC_KEY_2_FP
= SHA256:yBIKj17sF78/ndzDHEVxEmleCoGF+TdU6BrVECpFAW0=
```

Cette rotation a permis d'invalider uniquement la clé exposée sans casser l'accès du premier PC.

---

## 7. Protection du fichier `.env`

Avant d'y stocker la connexion Snowflake, il a été vérifié que `.env` est exclu de Git et du contexte Docker :

```bash
grep -nE '^\.env$|^\.env\*' .gitignore .dockerignore
```

Résultat :

```text
.gitignore:2:.env
.dockerignore:3:.env
```

La clé privée ne sera donc ni versionnée ni intégrée dans l'image Docker.

---

## 8. Connexion Airflow vers Snowflake

Le contenu de la clé privée a été transformé en une seule ligne :

```bash
PEM_ONE_LINE=$(awk 'NF {printf "%s\\n", $0}' ~/.ssh/snowflake/rsa_key.p8)
```

Le fichier `airflow/.env` contient la variable :

```text
AIRFLOW_CONN_SNOWFLAKE_NYC_TAXI
```

La connexion Airflow utilise :

```text
conn_type = snowflake
login     = AIRFLOW_SVC
schema    = RAW
account   = KWJSUAI-TM59629
warehouse = NYC_TAXI_WH
database  = NYC_TAXI
role      = TRANSFORMER
```

La clé privée est fournie via `private_key_content`, mais aucun secret n'est écrit dans le DAG.

---

## 9. Problème BuildKit / Buildx

Le premier démarrage Astro a échoué avec :

```text
the --mount option requires BuildKit
```

Le builder Docker historique était encore utilisé sur ce PC.

Le plugin Buildx a été installé :

```bash
sudo apt install docker-buildx
```

Vérification :

```bash
docker buildx version
```

Résultat :

```text
github.com/docker/buildx 0.30.1 0.30.1-0ubuntu1
```

Après cela, Astro a pu construire correctement l'image Airflow.

---

## 10. Démarrage d'Airflow

Commande :

```bash
astro dev start
```

Résultat :

```text
✔ Project image has been updated
✔ Project started
➤ Airflow UI: http://airflow.localhost:6563
➤ Postgres Database: postgresql://localhost:...
```

L'interface Airflow était accessible et fonctionnelle.

Après modification du `.env`, Astro a été redémarré avec :

```bash
astro dev restart
```

afin que les nouvelles variables d'environnement soient relues.

---

## 11. DAG de test Snowflake

Le fichier :

```text
dags/test_snowflake_connection.py
```

a été créé pour tester uniquement la connexion.

```python
import pendulum

from airflow.providers.snowflake.hooks.snowflake import SnowflakeHook
from airflow.sdk import dag, task


CONN_ID = "snowflake_nyc_taxi"


@dag(
    dag_id="test_snowflake_connection",
    schedule=None,
    start_date=pendulum.datetime(2025, 1, 1, tz="UTC"),
    catchup=False,
)
def test_snowflake_connection():

    @task
    def check_connection() -> None:
        hook = SnowflakeHook(snowflake_conn_id=CONN_ID)

        result = hook.get_first(
            """
            SELECT
                CURRENT_USER(),
                CURRENT_ROLE(),
                CURRENT_WAREHOUSE(),
                CURRENT_DATABASE(),
                CURRENT_SCHEMA()
            """
        )

        print(result)

    check_connection()


test_snowflake_connection()
```

Vérification :

```bash
astro dev run dags list-import-errors
```

Résultat :

```text
No data found
```

Ici, cela signifie qu'aucune erreur d'import n'a été détectée.

---

## 12. Validation réelle de la connexion

Le DAG de test a été déclenché manuellement :

```bash
astro dev run dags trigger test_snowflake_connection
```

Puis contrôlé avec :

```bash
astro dev run dags list-runs test_snowflake_connection
```

Résultat :

```text
state = success
```

Dans les logs :

```text
('AIRFLOW_SVC', 'TRANSFORMER', 'NYC_TAXI_WH', 'NYC_TAXI', 'RAW')
```

La chaîne suivante est donc validée :

```text
Airflow
   ↓
snowflake_nyc_taxi
   ↓
clé privée
   ↓
AIRFLOW_SVC
   ↓
TRANSFORMER
   ↓
NYC_TAXI_WH
   ↓
NYC_TAXI.RAW
```

---

## 13. Compréhension de la date logique

Le DAG mensuel ne doit pas choisir son fichier avec la date actuelle.

À éviter :

```python
datetime.now()
```

Un run de février 2025 rejoué en octobre 2026 doit toujours traiter :

```text
yellow_tripdata_2025-02.parquet
```

Airflow fournit pour cela le contexte d'exécution :

```python
context = get_current_context()
month = context["data_interval_start"].strftime("%Y-%m")
```

Ainsi :

```text
run janvier 2025  → yellow_tripdata_2025-01.parquet
run février 2025 → yellow_tripdata_2025-02.parquet
run mars 2025    → yellow_tripdata_2025-03.parquet
```

Le pipeline reste donc rejouable dans le temps.

---

## 14. Création du DAG mensuel

Le DAG principal est :

```text
dags/nyc_taxi_monthly.py
```

Configuration :

```python
@dag(
    dag_id="nyc_taxi_monthly",
    schedule="@monthly",
    start_date=pendulum.datetime(2025, 1, 1, tz="UTC"),
    end_date=pendulum.datetime(2025, 3, 1, tz="UTC"),
    catchup=True,
    max_active_runs=1,
)
```

Signification :

```text
schedule="@monthly"  → un run par mois
start_date           → janvier 2025
end_date             → mars 2025
catchup=True         → création des runs historiques manquants
max_active_runs=1    → un mois traité à la fois
```

---

## 15. Tâche `build_file_name`

```python
@task
def build_file_name() -> str:
    context = get_current_context()
    month = context["data_interval_start"].strftime("%Y-%m")

    file_name = f"yellow_tripdata_{month}.parquet"

    print(f"Logical month: {month}")
    print(f"File name: {file_name}")

    return file_name
```

Cette tâche transforme la date logique en nom de fichier source.

---

## 16. Tâche `check_file_exists`

```python
@task
def check_file_exists(file_name: str) -> str:
    url = f"{BASE_URL}/{file_name}"

    response = requests.head(url, timeout=30)
    response.raise_for_status()

    print(f"File available: {url}")

    return url
```

Avec :

```python
BASE_URL = "https://d37ci6vzurychx.cloudfront.net/trip-data"
```

La requête HTTP `HEAD` vérifie que le fichier existe avant de lancer le téléchargement complet.

---

## 17. Tâche `download_and_put`

```python
@task
def download_and_put(url: str) -> str:
    file_name = url.rsplit("/", 1)[-1]
    destination = Path("/tmp") / file_name

    try:
        with requests.get(url, stream=True, timeout=120) as response:
            response.raise_for_status()

            with destination.open("wb") as file:
                for chunk in response.iter_content(
                    chunk_size=8 * 1024 * 1024
                ):
                    if chunk:
                        file.write(chunk)

        hook = SnowflakeHook(snowflake_conn_id=CONN_ID)

        hook.run(
            f"""
            PUT file://{destination}
            @{STAGE}
            AUTO_COMPRESS=FALSE
            OVERWRITE=FALSE
            """
        )

        print(f"Uploaded to stage: {file_name}")

        return file_name

    finally:
        destination.unlink(missing_ok=True)
```

Cette tâche réalise :

```text
GET du Parquet
   ↓
écriture dans /tmp
   ↓
PUT vers le stage Snowflake
   ↓
suppression du fichier temporaire
```

Le téléchargement et le `PUT` restent dans la même tâche afin de ne pas dépendre d'un stockage local partagé entre plusieurs workers.

---

## 18. Connexion Snowflake dans le DAG

Les constantes utilisées sont :

```python
CONN_ID = "snowflake_nyc_taxi"
STAGE = "NYC_TAXI.RAW.NYC_TAXI_STAGE"
```

Le hook est créé avec :

```python
SnowflakeHook(snowflake_conn_id=CONN_ID)
```

Airflow récupère donc automatiquement la connexion configurée dans `.env`.

Aucun secret n'est codé dans le DAG.

---

## 19. Tâche `copy_into_raw`

```python
@task
def copy_into_raw(file_name: str) -> None:
    hook = SnowflakeHook(snowflake_conn_id=CONN_ID)

    hook.run(
        f"""
        COPY INTO NYC_TAXI.RAW.YELLOW_TRIPDATA
        FROM @{STAGE}
        FILES = ('{file_name}')
        FILE_FORMAT = (
            FORMAT_NAME = NYC_TAXI.RAW.PARQUET_FF
        )
        MATCH_BY_COLUMN_NAME = CASE_INSENSITIVE
        INCLUDE_METADATA = (
            _source_file = METADATA$FILENAME,
            _loaded_at = METADATA$START_SCAN_TIME
        )
        ON_ERROR = ABORT_STATEMENT
        """
    )

    print(f"Copied into RAW: {file_name}")
```

Cette tâche reprend les mêmes options que celles validées au Jour 2 :

```text
PARQUET_FF
MATCH_BY_COLUMN_NAME = CASE_INSENSITIVE
_source_file
_loaded_at
ON_ERROR = ABORT_STATEMENT
```

Le contrat RAW reste donc respecté.

---

## 20. Graphe final du DAG

La dépendance finale est :

```text
build_file_name
        ↓
check_file_exists
        ↓
download_and_put
        ↓
copy_into_raw
```

Le code de chaînage est :

```python
file_name = build_file_name()
url = check_file_exists(file_name)
staged_file = download_and_put(url)
copy_into_raw(staged_file)
```

Airflow construit automatiquement les dépendances à partir des valeurs retournées par les tâches.

---

## 21. XCom

Les tâches échangent uniquement de petites valeurs :

```text
nom du fichier
URL
nom du fichier du stage
```

Exemple :

```text
yellow_tripdata_2025-03.parquet
```

Le Parquet lui-même n'est jamais transmis dans XCom.

Règle retenue :

```text
petites métadonnées → XCom
gros fichier        → stockage temporaire / stage
```

---

## 22. Activation et `catchup`

Le DAG a été laissé en pause pendant sa construction.

Vérification :

```bash
astro dev run dags list | grep nyc_taxi_monthly
```

Avant activation :

```text
True
```

signifiait :

```text
paused
```

Après activation :

```text
False
```

signifiait :

```text
unpaused
```

Le scheduler a alors automatiquement créé les runs historiques.

---

## 23. Runs historiques

Commande :

```bash
astro dev run dags list-runs nyc_taxi_monthly
```

Les runs créés étaient :

```text
scheduled__2025-01-01T00:00:00+00:00
scheduled__2025-02-01T00:00:00+00:00
scheduled__2025-03-01T00:00:00+00:00
```

État final :

```text
2025-01 → success
2025-02 → success
2025-03 → success
```

Avec :

```python
max_active_runs=1
```

les mois ont été traités l'un après l'autre.

---

## 24. Idempotence sur janvier et février

Janvier et février avaient déjà été chargés au Jour 2.

Airflow les a rejoués sans créer de doublons.

Comportement :

```text
janvier
→ fichier déjà présent
→ chargement déjà connu
→ aucune ligne supplémentaire

février
→ fichier déjà présent
→ chargement déjà connu
→ aucune ligne supplémentaire
```

Mars a été ajouté pour la première fois par Airflow.

Ce test confirme que le pipeline peut être rejoué sans doubler les fichiers déjà chargés.

---

## 25. Vérification finale dans Snowflake

Requête :

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
yellow_tripdata_2025-01.parquet → 3 475 226
yellow_tripdata_2025-02.parquet → 3 577 543
yellow_tripdata_2025-03.parquet → 4 145 257
```

Total :

```text
3 475 226
+ 3 577 543
+ 4 145 257
-----------
11 198 026
```

La table :

```text
NYC_TAXI.RAW.YELLOW_TRIPDATA
```

contient donc exactement :

```text
11 198 026 lignes
```

après les trois mois.

---

## 26. Architecture finale du Jour 3

```text
                         AIRFLOW
                            │
                            │ date logique
                            ▼
                  build_file_name
                            │
                            ▼
                  check_file_exists
                            │
                            │ HTTP HEAD
                            ▼
                     NYC Open Data
                            │
                            │ HTTP GET
                            ▼
                  download_and_put
                            │
                            ├── fichier /tmp
                            │
                            └── PUT
                                │
                                ▼
                    NYC_TAXI_STAGE
                                │
                                │ COPY INTO
                                ▼
                  RAW.YELLOW_TRIPDATA
```

Snowflake reste responsable du stockage et du chargement dans RAW.

Airflow devient responsable de :

```text
quand exécuter
dans quel ordre
pour quel mois logique
avec quelles dépendances
avec quel statut
et comment rejouer l'historique
```

---

## 27. Ce que le Jour 3 a permis d'apprendre

Le point central de la journée est qu'Airflow ne remplace ni Python ni Snowflake.

Airflow orchestre des opérations existantes.

Au Jour 2 :

```text
Python
→ téléchargement
→ PUT
→ COPY INTO
```

Au Jour 3 :

```text
Airflow
→ task
→ task
→ task
→ task
```

Airflow ajoute :

```text
planification
date logique
dépendances
logs
statuts
historique
catchup
rejeu
```

La transformation et le stockage restent exécutés par les outils spécialisés.

---

## État final du Jour 3

```text
Astro CLI installé                               ✅
Projet Astro initialisé                          ✅
Airflow démarré                                  ✅
Provider Snowflake disponible                    ✅
Connexion Snowflake sécurisée                    ✅
Authentification par paire de clés               ✅
Deuxième clé dédiée au second PC                 ✅
Clé exposée révoquée puis renouvelée             ✅
DAG de test Snowflake                            ✅
Connexion AIRFLOW_SVC validée                    ✅
Date logique comprise                            ✅
DAG mensuel créé                                 ✅
Vérification HTTP du fichier                     ✅
Téléchargement automatique                       ✅
PUT vers le stage                                ✅
COPY INTO RAW                                    ✅
Colonnes techniques conservées                   ✅
Idempotence janvier                              ✅
Idempotence février                              ✅
Chargement mars                                  ✅
Catchup Airflow                                  ✅
Trois runs success                               ✅
RAW.YELLOW_TRIPDATA = 11 198 026 lignes          ✅
```

## Résultat final

```text
RAW.YELLOW_TRIPDATA
├── janvier 2025 : 3 475 226 lignes
├── février 2025 : 3 577 543 lignes
└── mars 2025    : 4 145 257 lignes

TOTAL
└── 11 198 026 lignes
```

Les trois exécutions Airflow sont en succès :

```text
2025-01 ✅
2025-02 ✅
2025-03 ✅
```

Le Jour 3 est terminé.
