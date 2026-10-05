Le script fonctionne bien, et il a déjà révélé plusieurs choses utiles. Le point principal à corriger maintenant est **l’affichage DuckDB** : certaines requêtes ont bien calculé toutes les colonnes, mais le CLI en masque une partie avec `…`. Par exemple, l’audit des anomalies produit 7 métriques, mais seulement 3 sont visibles. Texte collé

Ce qu’on peut déjà valider :

- **3 475 226 lignes** : c’est exactement le résultat attendu par le brief. Texte collé
- **20 colonnes**. Texte collé
- fichier d’environ **57 MiB / 59 158 238 octets**. Texte collé
- les types Parquet et les types interprétés par DuckDB sont correctement récupérés. Texte collé
- déjà quelques anomalies intéressantes :
  - **22 pickups hors janvier** ; Texte collé
  - **540 149 `passenger_count` NULL**, soit 15,54 % du fichier ; Texte collé
  - **124 trajets avec dropoff avant pickup**. Texte collé
- les différentes valeurs de codes ont bien été recensées. Texte collé

Donc **l’audit est bon**, mais avant de remplir la fiche je corrigerais juste sa lisibilité.

### Étape suivante uniquement : empêcher DuckDB de masquer les colonnes

Remplace ta fonction :

```bash
duckdb_query() {
    docker compose run --rm "$DUCKDB_SERVICE" -c "$1"
}
```

par :

```bash
duckdb_query() {
    docker compose run --rm "$DUCKDB_SERVICE" \
        -c ".mode line" \
        -c "$1"
}
```

Avec le mode `line`, au lieu d’avoir :

```text
distance_null │ … │ passenger_count_null │ ...
```

tu devrais obtenir quelque chose du genre :

```text
distance_null = ...
distance_zero = ...
distance_negative = ...
fare_negative = ...
total_negative = ...
passenger_count_null = 540149
dropoff_before_pickup = 124
```

C’est moins joli pour les tableaux, mais **beaucoup mieux pour un audit**, car aucune valeur importante ne disparaît.

Relance ensuite simplement :

```bash
./audit_parquet.sh yellow_tripdata_2025-01.parquet
```

et on regardera surtout les sections **6, 7 et 8** avant de remplir la fiche source.