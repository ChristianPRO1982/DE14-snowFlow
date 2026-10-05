# Fiche source - Trajets NYC Yellow Taxi

Une fiche par source de donnees. Tout chiffre indique comme mesure provient de l'audit local du fichier Parquet `parquet/yellow_tripdata_2025-01.parquet`.

## Identite

| Rubrique | Reponse |
|---|---|
| Nom de la source | NYC Yellow Taxi Trip Records |
| Producteur des donnees | NYC Taxi & Limousine Commission (TLC) |
| Adresse (URL) | https://d37ci6vzurychx.cloudfront.net/trip-data/yellow_tripdata_2025-01.parquet |
| Acces (public, authentifie) | Public, sans authentification |
| Format du fichier | Parquet |
| Frequence de publication | Mensuelle |
| Delai entre la periode couverte et la publication | Non mesure dans l'audit local |

## Volume mesure

| Fichier | Taille | Nombre de lignes | Nombre de colonnes | Outil et commande utilises |
|---|---:|---:|---:|---|
| `yellow_tripdata_2025-01.parquet` | 59 158 238 octets, environ 57 MiB | 3 475 226 | 20 | `cd parquet && ./audit_parquet.sh yellow_tripdata_2025-01.parquet` |

## Colonnes

| Colonne | Type dans le fichier | Signification | Exemple de valeur |
|---|---|---|---|
| `VendorID` | Entier | Fournisseur ayant transmis l'enregistrement du trajet | `1` |
| `tpep_pickup_datetime` | Timestamp | Date et heure de prise en charge du passager | `2025-01-01 00:00:00` |
| `tpep_dropoff_datetime` | Timestamp | Date et heure de depose du passager | `2025-01-01 00:15:00` |
| `passenger_count` | Entier | Nombre de passagers declares par le chauffeur | `1` |
| `trip_distance` | Decimal | Distance du trajet en miles | `1.67` |
| `RatecodeID` | Entier | Code tarifaire applique au trajet | `1` |
| `store_and_fwd_flag` | Texte | Indique si le trajet a ete stocke avant transmission | `N` |
| `PULocationID` | Entier | Identifiant de la zone TLC de prise en charge | `161` |
| `DOLocationID` | Entier | Identifiant de la zone TLC de depose | `236` |
| `payment_type` | Entier | Code du mode de paiement | `1` |
| `fare_amount` | Decimal | Montant de base de la course | `12.27` |
| `extra` | Decimal | Supplements appliques au trajet | `1.00` |
| `mta_tax` | Decimal | Taxe MTA | `0.50` |
| `tip_amount` | Decimal | Pourboire | `3.00` |
| `tolls_amount` | Decimal | Montant des peages | `0.00` |
| `improvement_surcharge` | Decimal | Supplement d'amelioration | `1.00` |
| `total_amount` | Decimal | Montant total facture | `19.96` |
| `congestion_surcharge` | Decimal | Supplement de congestion | `2.50` |
| `Airport_fee` | Decimal | Supplement aeroport | `0.00` |
| `cbd_congestion_fee` | Decimal | Supplement de congestion CBD | `0.00` |

## Codes

Les codes ci-dessous reprennent les tables de reference TLC fournies dans le starter kit (`airflow/include/sql/staging/codes_tlc.sql`) et les valeurs observees dans l'audit de janvier 2025.

| Colonne | Valeur | Signification |
|---|---:|---|
| `VendorID` | `1` | Creative Mobile Technologies, LLC |
| `VendorID` | `2` | Curb Mobility, LLC |
| `VendorID` | `6` | Myle Technologies Inc |
| `VendorID` | `7` | Helix |
| `RatecodeID` | `1` | Standard rate |
| `RatecodeID` | `2` | JFK |
| `RatecodeID` | `3` | Newark |
| `RatecodeID` | `4` | Nassau or Westchester |
| `RatecodeID` | `5` | Negotiated fare |
| `RatecodeID` | `6` | Group ride |
| `RatecodeID` | `99` | Null or unknown |
| `RatecodeID` | `NULL` | Valeur manquante observee dans le fichier |
| `payment_type` | `0` | Flex Fare trip |
| `payment_type` | `1` | Credit card |
| `payment_type` | `2` | Cash |
| `payment_type` | `3` | No charge |
| `payment_type` | `4` | Dispute |
| `payment_type` | `5` | Unknown |
| `payment_type` | `6` | Voided trip |
| `store_and_fwd_flag` | `N` | Trajet transmis directement, non stocke avant transmission |
| `store_and_fwd_flag` | `Y` | Trajet stocke en memoire avant transmission |
| `store_and_fwd_flag` | `NULL` | Valeur manquante observee dans le fichier |

## Ce qui a surpris

- Le fichier de janvier contient des trajets hors periode : pickup minimum `2024-12-31 20:47:55`, pickup maximum `2025-02-01 00:00:44`, et 22 trajets ont une date de prise en charge hors janvier.
- Plusieurs colonnes contiennent beaucoup de valeurs manquantes : `passenger_count`, `RatecodeID`, `store_and_fwd_flag`, `congestion_surcharge` et `Airport_fee` ont chacune 540 149 valeurs `NULL`, soit 15,54 % des lignes.
- Certaines valeurs sont atypiques ou incoherentes : 90 893 trajets ont une distance egale a 0, 63 037 lignes ont un `total_amount` negatif, et 124 lignes ont une date de depose anterieure a la date de prise en charge.
