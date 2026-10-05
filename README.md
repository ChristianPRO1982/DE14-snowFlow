# DE14 SnowFlow + Airflow

Pipeline medaillon NYC Yellow Taxi avec Snowflake et Airflow.

Ce depot repond au brief `Pipeline medaillon NYC Yellow Taxi : Snowflake et Airflow`.
L'objectif est de rendre rejouable l'ingestion mensuelle des fichiers publics TLC, puis les transformations et controles de qualite dans Snowflake via Airflow.

## Installation et verification locale

Il n'y a pas encore d'application a installer a la racine du depot. La premiere verification locale porte sur le fichier Parquet de janvier 2025, place dans :

```text
parquet/yellow_tripdata_2025-01.parquet
```

Le dossier `parquet/` contient un environnement DuckDB lance avec Docker Compose pour lire le fichier sans installer DuckDB sur la machine.

### Prerequis

- Docker
- Docker Compose

### Lancer DuckDB

```bash
cd parquet
docker compose run --rm duckdb
```

Dans le shell DuckDB :

```sql
.read explore.sql
```

### Executer un test rapide

```bash
cd parquet
docker compose run --rm duckdb -c "SELECT COUNT(*) FROM read_parquet('yellow_tripdata_2025-01.parquet');"
```

Le resultat attendu pour janvier 2025 est :

```text
3 475 226 lignes
```

### Auditer le fichier Parquet

Un script d'audit local mesure le volume, inspecte le schema, affiche des exemples, liste les codes observes et repere des valeurs surprenantes.

```bash
cd parquet
./audit_parquet.sh yellow_tripdata_2025-01.parquet
```

Pour ne pas surcharger ce README, le compte rendu detaille de l'audit est conserve dans [parquet/audit_results.md](parquet/audit_results.md).

## Jour 1 - Comprendre le pipeline et explorer la source

La source analysee est le fichier public TLC des trajets Yellow Taxi de janvier 2025 :

```text
https://d37ci6vzurychx.cloudfront.net/trip-data/yellow_tripdata_2025-01.parquet
```

Premiers constats mesures localement avec DuckDB :

| Mesure | Valeur |
|---|---:|
| Format | Parquet |
| Taille | 59 158 238 octets, environ 57 MiB |
| Nombre de lignes | 3 475 226 |
| Nombre de colonnes | 20 |

Quelques points de qualite identifies pendant l'exploration :

- 22 trajets ont une date de prise en charge hors janvier 2025.
- 540 149 lignes ont `passenger_count` a `NULL`.
- 124 lignes ont une date de depose anterieure a la date de prise en charge.

Ces observations confirment que les donnees sont exploitables, mais qu'elles doivent passer par une couche de nettoyage et de controle avant d'alimenter les tables d'analyse.

## Jour 2 - Charger les fichiers dans RAW

A completer avec les scripts Snowflake de creation de la couche RAW, le stage, les formats de fichier et le chargement rejouable.

Resultat attendu :

- `RAW.YELLOW_TRIPDATA` contient 3 475 226 lignes pour janvier.
- `RAW.TAXI_ZONE_LOOKUP` contient 265 zones.
- Une relance du chargement ne cree pas de doublons.

## Jour 3 - Automatiser le chargement avec Airflow

A completer avec le DAG Airflow qui deduit le mois a charger depuis la date logique, telecharge le fichier TLC, le depose sur le stage Snowflake et lance le `COPY INTO`.

Resultat attendu :

- Les executions de janvier, fevrier et mars 2025 sont reussies.
- Le pipeline ne depend pas de la date du jour.

## Jour 4 - Transformer et controler

A completer avec l'ordre d'execution des fichiers SQL fournis, les groupes de taches Airflow par couche et les controles de qualite.

Resultat attendu :

- Les transformations alimentent les couches `STAGING`, `INTERMEDIATE` et `MARTS`.
- Les controles bloquent la suite du pipeline en cas d'anomalie.
- `MARTS.FCT_TRIPS` contient 10 382 378 trajets valides apres les trois mois.

## Jour 5 - Reponse metier et presentation

A completer avec la requete finale, le top zones x heures, les commentaires pour la direction, les controles d'anomalies et les elements de demonstration.

La reponse finale sera documentee dans `docs/REPONSE.md`.
