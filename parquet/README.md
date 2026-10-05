# Exploration locale du parquet avec DuckDB

Depuis ce dossier :

```bash
cd parquet
docker compose run --rm duckdb
```

Puis, dans le shell DuckDB :

```sql
.read explore.sql
```

Commande directe sans shell interactif :

```bash
docker compose run --rm duckdb -c "SELECT COUNT(*) FROM read_parquet('yellow_tripdata_2025-01.parquet');"
```

Audit complet du fichier :

```bash
chmod +x audit_parquet.sh
./audit_parquet.sh yellow_tripdata_2025-01.parquet
```

Le fichier `yellow_tripdata_2025-01.parquet` est monté dans le conteneur sous `/data`.
