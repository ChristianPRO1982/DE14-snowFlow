# Analyse du fichier `yellow_tripdata_2025-01.parquet`

## Vue d’ensemble

Le fichier contient **3 475 226 lignes**, **20 colonnes** et pèse **59 158 238 octets (~57 MiB)**. Ces valeurs sont cohérentes avec le volume attendu pour le mois de janvier. Texte collé

Les types sont globalement cohérents avec la nature des données : timestamps pour les dates, entiers pour les identifiants/codes, nombres décimaux pour les distances et montants. Texte collé

## Points d’attention

### 1. Des données hors de la période de janvier

Le fichier contient des dates en dehors de janvier 2025 :

- pickup minimum : `2024-12-31 20:47:55`
- pickup maximum : `2025-02-01 00:00:44`
- dropoff minimum : `2024-12-18 07:52:40`
- dropoff maximum : `2025-02-01 23:44:11`
- **22 trajets ont un pickup hors janvier**. Texte collé

Le fichier mensuel ne peut donc pas être considéré comme strictement limité à janvier sur la seule base de son nom.

### 2. Valeurs manquantes sur plusieurs colonnes

`passenger_count` contient **540 149 valeurs NULL**, soit **15,54 %** des lignes. Le même taux de valeurs manquantes apparaît notamment sur `RatecodeID`, `store_and_fwd_flag`, `congestion_surcharge` et `Airport_fee`. Texte collé Texte collé Texte collé

Cette proportion est suffisamment importante pour nécessiter une prise en compte explicite dans les traitements ultérieurs.

### 3. Distances nulles ou extrêmes

Aucune distance négative n’a été détectée, mais **90 893 trajets ont une distance égale à 0**. Texte collé

La valeur maximale de `trip_distance` atteint **276 423,57**, alors que la médiane est d’environ **1,67**. Cette valeur extrême est très éloignée de la distribution générale et devra être filtrée ou contrôlée par les règles métier. Texte collé

### 4. Montants négatifs

Plusieurs montants sont négatifs :

- **144 118** lignes avec `fare_amount < 0`
- **63 037** lignes avec `total_amount < 0`. Texte collé

Les statistiques montrent également des valeurs négatives pour plusieurs composantes tarifaires, notamment `extra`, `mta_tax`, `tip_amount`, `tolls_amount`, `improvement_surcharge`, `congestion_surcharge` et `Airport_fee`. Texte collé Texte collé

Ces valeurs ne doivent donc pas être supposées positives en couche RAW.

### 5. Montants extrêmement élevés

Certaines valeurs maximales sont très élevées :

- `fare_amount` : **863 372,12**
- `total_amount` : **863 380,37**. Texte collé Texte collé

Ces valeurs sont très éloignées des médianes respectives, environ **12,27** pour `fare_amount` et **19,96** pour `total_amount`. Elles constituent des valeurs atypiques à contrôler.

### 6. Incohérences temporelles

**124 lignes** présentent un `tpep_dropoff_datetime` antérieur au `tpep_pickup_datetime`. Texte collé

Ces trajets sont temporellement incohérents et devront être identifiés par les règles de qualité.

### 7. Codes observés à vérifier avec le dictionnaire TLC

Plusieurs codes sont présents dans les données :

- `RatecodeID` contient notamment `1` à `6`, `99` et `NULL`;
- `VendorID` contient `1`, `2`, `6` et `7`;
- `payment_type` contient `0` à `5`;
- `store_and_fwd_flag` contient `N`, `Y` et `NULL`. Texte collé

Leur présence est factuelle, mais leur signification ne peut pas être déduite du fichier seul : elle doit être vérifiée dans le dictionnaire officiel TLC.

## Conclusion

Le fichier est exploitable techniquement et son schéma est cohérent, mais il contient plusieurs catégories d’anomalies : **dates hors période, valeurs NULL, distances nulles ou extrêmes, montants négatifs ou très élevés et incohérences temporelles**.

Ces anomalies justifient pleinement la séparation prévue par l’architecture :

```text
RAW
→ conservation fidèle des données source

STAGING / INTERMEDIATE
→ typage, contrôles et application des règles métier
```

Aucune de ces anomalies ne justifie de modifier les données en RAW ; elles doivent être conservées puis traitées dans les couches suivantes.