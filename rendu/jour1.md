# Compte rendu — Jour 1

```text
1. Comprendre l’architecture                    ✅
2. Explorer janvier + fiche source              ✅
3. Suivre le guide SALES_DB                     ✅
4. Écrire l’infrastructure NYC_TAXI             ✅
5. Générer les clés + tester AIRFLOW_SVC        ✅
```

## Objectif du jour

Le premier jour avait pour objectif de comprendre l’architecture générale du pipeline, d’explorer la source principale de données, puis de mettre en place l’infrastructure Snowflake de base avec une gestion correcte des rôles, des droits et d’un utilisateur de service authentifié par paire de clés.

Le script d’infrastructure créé pour le projet est versionné dans :

```text
snowflake/01_infrastructure.sql
```

---

## 1. Compréhension de l’architecture

Le pipeline repose sur deux sources :

- les fichiers mensuels Parquet des NYC Yellow Taxi Trip Records publiés par la NYC Taxi & Limousine Commission ;
- le fichier CSV de référence des zones de taxi fourni dans le brief.

Le parcours principal des données est :

```text
NYC TLC
  ↓
fichier Parquet mensuel
  ↓
Airflow / Python
  ↓
Snowflake Stage
  ↓
RAW
  ↓
STAGING
  ↓
INTERMEDIATE
  ↓
MARTS
```

Rôle des couches :

- `RAW` : conservation fidèle des données source avec ajout de colonnes techniques ;
- `STAGING` : mise en forme technique et normalisation des données ;
- `INTERMEDIATE` : application des règles métier, contrôles et enrichissements ;
- `MARTS` : données prêtes à être exploitées pour l’analyse et le reporting.

Airflow joue le rôle d’orchestrateur : il ne stocke pas les données, mais pilote les tâches de chargement, transformation et contrôle.

---

## 2. Exploration du fichier de janvier 2025

Le fichier analysé est :

```text
yellow_tripdata_2025-01.parquet
```

Résultats principaux :

- 3 475 226 lignes ;
- 20 colonnes ;
- environ 57 MiB ;
- données globalement cohérentes avec le schéma attendu.

Plusieurs anomalies ont été observées :

- 22 trajets avec une date de prise en charge hors janvier ;
- 540 149 valeurs `NULL` sur plusieurs colonnes, soit environ 15,54 % ;
- 90 893 trajets avec une distance égale à `0` ;
- valeurs extrêmes sur `trip_distance` ;
- montants négatifs sur `fare_amount` et `total_amount` ;
- valeurs tarifaires anormalement élevées ;
- 124 trajets avec une date de dépose antérieure à la date de prise en charge.

Ces observations confirment l’intérêt de conserver les données telles quelles dans `RAW`, puis de gérer la qualité et les règles métier dans les couches suivantes.

La fiche source complétée est stockée dans :

```text
docs/fiche_trajets.md
```

---

## 3. Exercice de sécurité Snowflake avec `SALES_DB`

Avant de créer l’infrastructure réelle, le guide Snowflake a été reproduit sur un environnement d’exercice.

Objets créés :

```text
SALES_WH

SALES_DB
├── RAW_DATA
└── ANALYTICS
```

Rôles :

```text
SALES_ENGINEER
SALES_ANALYST
```

Principes appris :

- les privilèges sont donnés à des rôles, puis les rôles aux utilisateurs ;
- `USERADMIN` sert principalement à gérer les rôles et les utilisateurs ;
- `SYSADMIN` sert à gérer les objets Snowflake ;
- l’accès à une table dépend d’une chaîne de droits sur le warehouse, la base, le schéma et la table ;
- les `FUTURE GRANTS` permettent d’appliquer automatiquement des droits sur les futurs objets ;
- le principe du moindre privilège doit être privilégié.

Exemple validé :

```text
SALES_ENGINEER
  → peut créer une table dans ANALYTICS

SALES_ANALYST
  → peut lire cette table
  → ne peut pas créer de table
```

Une tentative de création de table avec `SALES_ANALYST` a bien échoué avec une erreur de droits insuffisants.

---

## 4. Infrastructure réelle `NYC_TAXI`

L’infrastructure réelle du brief a ensuite été créée dans :

```text
snowflake/01_infrastructure.sql
```

### Rôle outil

Le rôle suivant a été créé :

```text
TRANSFORMER
```

Il est rattaché à :

```text
SYSADMIN
```

### Warehouse

Le warehouse utilisé pour le projet est :

```text
NYC_TAXI_WH
```

Configuration :

```text
size         = X-Small
auto_suspend = 60
auto_resume  = true
owner        = SYSADMIN
```

Le warehouse est automatiquement suspendu après 60 secondes d’inactivité afin de limiter la consommation de crédits.

### Base et schémas

La base créée est :

```text
NYC_TAXI
```

avec les quatre schémas imposés par le brief :

```text
NYC_TAXI
├── RAW
├── STAGING
├── INTERMEDIATE
└── MARTS
```

### Droits de `TRANSFORMER`

Le rôle `TRANSFORMER` possède les droits nécessaires au pipeline.

Sur le warehouse :

```text
USAGE
OPERATE
```

Sur la base :

```text
USAGE
```

Sur `RAW` :

```text
USAGE
CREATE TABLE
CREATE STAGE
CREATE FILE FORMAT
```

Sur `STAGING`, `INTERMEDIATE` et `MARTS` :

```text
USAGE
CREATE TABLE
CREATE VIEW
```

Cette configuration respecte le principe du moindre privilège.

---

## 5. Utilisateur de service et authentification par paire de clés

L’utilisateur de service créé pour Airflow est :

```text
AIRFLOW_SVC
```

Il utilise par défaut :

```text
role      = TRANSFORMER
warehouse = NYC_TAXI_WH
namespace = NYC_TAXI.RAW
```

Le rôle lui a été explicitement attribué :

```text
AIRFLOW_SVC
  ↓
TRANSFORMER
```

### Paire de clés

Une paire de clés RSA a été générée localement :

```text
~/.ssh/snowflake/rsa_key.p8
~/.ssh/snowflake/rsa_key.pub
```

Permissions de la clé privée :

```text
-rw-------
```

La clé privée reste sur le poste local et n’est jamais envoyée dans Git ni intégrée dans une image Docker.

La clé publique a été enregistrée sur l’utilisateur Snowflake `AIRFLOW_SVC`.

L’empreinte locale de la clé publique a été comparée à l’empreinte enregistrée dans Snowflake et les deux correspondent.

---

## 6. Test final depuis Docker

Le test de connexion a été réalisé depuis un conteneur Docker jetable afin de rester proche de l’architecture cible du projet.

La clé privée est montée en lecture seule dans le conteneur.

Commande utilisée :

```bash
docker run --rm -i \
  -v "$HOME/.ssh/snowflake/rsa_key.p8:/run/secrets/rsa_key.p8:ro" \
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
)

result = conn.cursor().execute(
    """
    SELECT
        CURRENT_USER(),
        CURRENT_ROLE(),
        CURRENT_WAREHOUSE(),
        CURRENT_DATABASE(),
        CURRENT_SCHEMA()
    """
).fetchone()

print(result)
conn.close()
PY
```

Résultat obtenu :

```text
('AIRFLOW_SVC', 'TRANSFORMER', 'NYC_TAXI_WH', 'NYC_TAXI', 'RAW')
```

Ce résultat valide :

- l’identifiant du compte Snowflake ;
- l’utilisateur de service ;
- l’authentification par paire de clés ;
- le rôle `TRANSFORMER` ;
- l’accès au warehouse `NYC_TAXI_WH` ;
- le contexte par défaut `NYC_TAXI.RAW` ;
- la capacité d’un environnement Dockerisé à se connecter à Snowflake.

---

## Conclusion

Le Jour 1 est terminé avec une infrastructure Snowflake fonctionnelle et sécurisée.

Les éléments principaux sont maintenant en place :

```text
Docker / futur Airflow
        ↓
AIRFLOW_SVC
        ↓
TRANSFORMER
        ↓
NYC_TAXI_WH
        ↓
NYC_TAXI
├── RAW
├── STAGING
├── INTERMEDIATE
└── MARTS
```

Le projet est prêt pour la suite du brief, qui consistera à construire la couche `RAW` et à charger les premières données.
