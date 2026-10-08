# Mini-cours — Sécurité Snowflake : rôles, droits et objets

## 1. Objectif

Avant de construire le pipeline NYC Taxi, l’objectif de cet exercice est de comprendre le modèle de sécurité de Snowflake avec une petite infrastructure de démonstration :

```text
SALES_DB
├── RAW_DATA
└── ANALYTICS

Warehouse : SALES_WH

Rôles :
├── SALES_ENGINEER
└── SALES_ANALYST
```

L’idée générale est d’appliquer du **RBAC — Role-Based Access Control** :

```text
Utilisateur
    │ possède
    ▼
   Rôle
    │ reçoit des
    ▼
Privilèges
    │ sur des
    ▼
  Objets
```

On évite donc de donner directement des permissions à chaque utilisateur. Les privilèges sont principalement attribués aux rôles, puis les rôles sont attribués aux utilisateurs. 

---

## 2. Les rôles système principaux

Snowflake fournit plusieurs rôles administratifs.

| Rôle | Utilité |
|---|---|
| `ACCOUNTADMIN` | Administration globale du compte |
| `USERADMIN` | Gestion des utilisateurs et des rôles |
| `SYSADMIN` | Gestion des objets : warehouses, bases, schémas… |
| `PUBLIC` | Rôle commun automatiquement disponible |

Une bonne pratique consiste à éviter d'utiliser `ACCOUNTADMIN` pour les opérations quotidiennes.

Dans notre exercice :

```text
USERADMIN
    ↓
crée les rôles

SYSADMIN
    ↓
crée les warehouses, bases et schémas
```

---

# 3. Vérifier son contexte Snowflake

Avant toute création, il est utile de savoir avec quelle identité et quel rôle la session travaille.

```sql
SELECT
    CURRENT_USER(),
    CURRENT_ROLE(),
    CURRENT_WAREHOUSE(),
    CURRENT_DATABASE(),
    CURRENT_SCHEMA();
```

Résultat obtenu :

| Élément | Valeur |
|---|---|
| User | `CHRISTIAN` |
| Role | `ACCOUNTADMIN` |
| Warehouse | `COMPUTE_WH` |
| Database | aucune |
| Schema | aucun |

Cela signifie que la session utilisait initialement le rôle très puissant `ACCOUNTADMIN`.

---

# 4. Attention au fonctionnement de Snowsight

Dans l'éditeur SQL Snowflake :

- **Play / Run** exécute uniquement l'instruction courante ou la sélection ;
- **Run All** exécute toutes les instructions dans l'ordre.

Cette distinction est importante avec des scripts contenant :

```sql
USE ROLE USERADMIN;

CREATE ROLE ...
```

Si seul le `CREATE ROLE` est exécuté alors que le rôle courant reste `ACCOUNTADMIN`, l'objet sera créé dans un contexte différent de celui prévu.

Le guide attire précisément l'attention sur ce comportement de Snowsight. 

---

# 5. Créer les rôles métier

On commence avec `USERADMIN`.

```sql
USE ROLE USERADMIN;

CREATE ROLE IF NOT EXISTS SALES_ENGINEER
  COMMENT = 'Rôle des outils : chargement et transformations';

CREATE ROLE IF NOT EXISTS SALES_ANALYST
  COMMENT = 'Lecture seule sur le schéma ANALYTICS';
```

Vérification :

```sql
SHOW ROLES LIKE 'SALES%';
```

Résultat obtenu :

```text
SALES_ENGINEER → owner = USERADMIN
SALES_ANALYST  → owner = USERADMIN
```

Le rôle actif au moment d'une création est important notamment pour la notion de **propriétaire**.

---

# 6. Hiérarchie des rôles

Les rôles personnalisés sont ensuite rattachés à `SYSADMIN`.

```sql
USE ROLE USERADMIN;

GRANT ROLE SALES_ENGINEER TO ROLE SYSADMIN;
GRANT ROLE SALES_ANALYST  TO ROLE SYSADMIN;
```

Vérification :

```sql
SHOW GRANTS OF ROLE SALES_ENGINEER;
SHOW GRANTS OF ROLE SALES_ANALYST;
```

Résultat :

```text
SALES_ENGINEER → SYSADMIN
SALES_ANALYST  → SYSADMIN
```

Cela forme notamment cette hiérarchie :

```text
SYSADMIN
├── SALES_ENGINEER
└── SALES_ANALYST
```

Snowflake permet ainsi à un rôle parent d'hériter des privilèges des rôles enfants. 

---

# 7. Warehouse ≠ base de données

Un point important dans le vocabulaire Snowflake :

> Un **warehouse** représente la puissance de calcul utilisée pour exécuter les requêtes.

Ce n'est donc pas l'endroit où les tables sont stockées.

Nous créons :

```text
SALES_WH = compute

SALES_DB = données
```

---

# 8. Création du warehouse et de la base

On utilise `SYSADMIN`.

```sql
USE ROLE SYSADMIN;

CREATE WAREHOUSE IF NOT EXISTS SALES_WH
  WAREHOUSE_SIZE = 'XSMALL'
  AUTO_SUSPEND = 60
  AUTO_RESUME = TRUE
  INITIALLY_SUSPENDED = TRUE;

CREATE DATABASE IF NOT EXISTS SALES_DB;

CREATE SCHEMA IF NOT EXISTS SALES_DB.RAW_DATA;
CREATE SCHEMA IF NOT EXISTS SALES_DB.ANALYTICS;
```

### Warehouse obtenu

```text
name         = SALES_WH
state        = SUSPENDED
size         = X-Small
auto_suspend = 60
auto_resume  = true
owner        = SYSADMIN
```

Le warehouse se suspend donc après 60 secondes d'inactivité, ce qui limite la consommation de crédits.

### Base obtenue

```text
SALES_DB
├── RAW_DATA
├── ANALYTICS
├── PUBLIC
└── INFORMATION_SCHEMA
```

`PUBLIC` et `INFORMATION_SCHEMA` sont créés automatiquement par Snowflake.

---

# 9. Principe de la chaîne de droits

Dans Snowflake, avoir `SELECT` sur une table ne suffit pas nécessairement.

Pour accéder à :

```text
SALES_DB.ANALYTICS.MA_TABLE
```

un rôle doit pouvoir traverser toute la hiérarchie.

Par exemple :

```text
USAGE sur Warehouse
+
USAGE sur Database
+
USAGE sur Schema
+
SELECT sur Table
```

On peut voir cela comme :

```text
SALES_WH
    ↓ USAGE

SALES_DB
    ↓ USAGE

ANALYTICS
    ↓ USAGE

TABLE
    ↓ SELECT
```

Le guide Snowflake insiste sur cette chaîne d'accès. 

---

# 10. Droits du rôle `SALES_ENGINEER`

`SALES_ENGINEER` représente ici un outil ou un Data Engineer ayant besoin de construire les objets du pipeline.

```sql
USE ROLE SYSADMIN;

GRANT USAGE, OPERATE
  ON WAREHOUSE SALES_WH
  TO ROLE SALES_ENGINEER;

GRANT USAGE
  ON DATABASE SALES_DB
  TO ROLE SALES_ENGINEER;

GRANT USAGE, CREATE TABLE, CREATE STAGE, CREATE FILE FORMAT
  ON SCHEMA SALES_DB.RAW_DATA
  TO ROLE SALES_ENGINEER;

GRANT USAGE, CREATE TABLE, CREATE VIEW
  ON SCHEMA SALES_DB.ANALYTICS
  TO ROLE SALES_ENGINEER;
```

Vérification :

```sql
SHOW GRANTS TO ROLE SALES_ENGINEER;
```

Résultat résumé :

```text
WAREHOUSE SALES_WH
├── USAGE
└── OPERATE

DATABASE SALES_DB
└── USAGE

RAW_DATA
├── USAGE
├── CREATE TABLE
├── CREATE STAGE
└── CREATE FILE FORMAT

ANALYTICS
├── USAGE
├── CREATE TABLE
└── CREATE VIEW
```

Le rôle dispose donc des droits nécessaires sans recevoir des privilèges administratifs globaux.

---

# 11. Droits du rôle `SALES_ANALYST`

L'analyste doit pouvoir utiliser les données, mais pas modifier la structure.

```sql
USE ROLE SYSADMIN;

GRANT USAGE
  ON WAREHOUSE SALES_WH
  TO ROLE SALES_ANALYST;

GRANT USAGE
  ON DATABASE SALES_DB
  TO ROLE SALES_ANALYST;

GRANT USAGE
  ON SCHEMA SALES_DB.ANALYTICS
  TO ROLE SALES_ANALYST;
```

Puis :

```sql
GRANT SELECT
  ON ALL TABLES IN SCHEMA SALES_DB.ANALYTICS
  TO ROLE SALES_ANALYST;

GRANT SELECT
  ON ALL VIEWS IN SCHEMA SALES_DB.ANALYTICS
  TO ROLE SALES_ANALYST;
```

---

# 12. `ALL` et `FUTURE`

Snowflake distingue les objets qui existent **maintenant** et ceux qui seront créés **plus tard**.

```text
ALL TABLES
    ↓
tables existantes

FUTURE TABLES
    ↓
tables créées plus tard
```

On ajoute donc :

```sql
GRANT SELECT
  ON FUTURE TABLES IN SCHEMA SALES_DB.ANALYTICS
  TO ROLE SALES_ANALYST;

GRANT SELECT
  ON FUTURE VIEWS IN SCHEMA SALES_DB.ANALYTICS
  TO ROLE SALES_ANALYST;
```

Vérification :

```sql
SHOW FUTURE GRANTS IN SCHEMA SALES_DB.ANALYTICS;
```

Résultat obtenu :

```text
SELECT → FUTURE TABLES → SALES_ANALYST
SELECT → FUTURE VIEWS  → SALES_ANALYST
```

Les droits futurs sont particulièrement utiles quand les outils reconstruisent régulièrement les tables. 

---

# 13. Vérifier réellement les permissions

Un `SHOW GRANTS` est utile, mais la meilleure preuve consiste à réellement effectuer les opérations.

## Création avec `SALES_ENGINEER`

```sql
USE ROLE SALES_ENGINEER;
USE WAREHOUSE SALES_WH;

CREATE TABLE SALES_DB.ANALYTICS.TEST (id INT);
```

La création fonctionne.

---

## Lecture avec `SALES_ANALYST`

```sql
USE ROLE SALES_ANALYST;
USE WAREHOUSE SALES_WH;

SELECT COUNT(*)
FROM SALES_DB.ANALYTICS.TEST;
```

Résultat :

```text
COUNT(*) = 0
```

La table est vide, mais la requête fonctionne.

Cela prouve que :

```text
SALES_ENGINEER crée TEST
        ↓
le FUTURE GRANT est appliqué
        ↓
SALES_ANALYST reçoit SELECT
        ↓
SALES_ANALYST peut lire TEST
```

---

# 14. Tester également ce qui doit être interdit

On tente ensuite :

```sql
USE ROLE SALES_ANALYST;

CREATE TABLE SALES_DB.ANALYTICS.TEST_ANALYST (id INT);
```

Résultat obtenu :

```text
SQL access control error:
Insufficient privileges to operate on schema 'ANALYTICS'.

Your primary role SALES_ANALYST must have CREATE TABLE granted
on SCHEMA SALES_DB.ANALYTICS.
```

C'est exactement le comportement recherché.

```text
SALES_ANALYST

SELECT        ✅
CREATE TABLE  ❌
```

C'est une application du **principe du moindre privilège** :

> Un rôle reçoit uniquement les permissions nécessaires à sa fonction.

---

# 15. Ownership : le créateur contrôle son objet

La table `TEST` a été créée avec :

```sql
USE ROLE SALES_ENGINEER;
```

`SALES_ENGINEER` peut donc également la supprimer :

```sql
USE ROLE SALES_ENGINEER;

DROP TABLE SALES_DB.ANALYTICS.TEST;
```

Puis :

```sql
SHOW TABLES IN SCHEMA SALES_DB.ANALYTICS;
```

Résultat :

```text
Query produced no results
```

La table a correctement été supprimée.

---

# 16. Architecture obtenue

À ce stade :

```text
                         SYSADMIN
                        /        \
                       /          \
          SALES_ENGINEER       SALES_ANALYST
                │                   │
                │                   │
                ▼                   ▼

SALES_WH
  ENGINEER : USAGE + OPERATE
  ANALYST  : USAGE


SALES_DB
│
├── RAW_DATA
│   └── ENGINEER
│       ├── CREATE TABLE
│       ├── CREATE STAGE
│       └── CREATE FILE FORMAT
│
└── ANALYTICS
    ├── ENGINEER
    │   ├── CREATE TABLE
    │   └── CREATE VIEW
    │
    └── ANALYST
        └── SELECT
```

---

# 17. Ce qu'il faut retenir

### RBAC

```text
Utilisateur
    ↓
Rôle
    ↓
Privilège
    ↓
Objet
```

### Séparation des responsabilités

```text
USERADMIN
→ rôles et utilisateurs

SYSADMIN
→ warehouse, bases, schémas

SALES_ENGINEER
→ construit les données

SALES_ANALYST
→ lit les données
```

### Chaîne d'accès

Pour travailler sur une table :

```text
warehouse
    ↓
database
    ↓
schema
    ↓
table
```

Les privilèges doivent être cohérents sur toute cette chaîne.

### Principe du moindre privilège

Un rôle ne reçoit que les droits dont il a réellement besoin.

```text
ENGINEER → construit
ANALYST  → lit
```

### Droits futurs

```text
ALL    = objets actuels
FUTURE = objets futurs
```

Dans un pipeline automatisé, les `FUTURE GRANTS` permettent de conserver automatiquement les droits lorsque de nouveaux objets sont créés.

---

# 18. Suite du cours

La prochaine notion sera l'**utilisateur de service** :

```text
SALES_ETL_SVC
      │
      ▼
SALES_ENGINEER
```

Contrairement à un utilisateur humain comme `CHRISTIAN`, cet utilisateur sera destiné aux programmes tels que Python ou Airflow.

Il ne s'authentifiera pas avec ton mot de passe mais avec une **paire de clés cryptographiques** :

```text
outil / Airflow
     │
clé privée
     │
     ▼
connexion signée
     │
     ▼
Snowflake
     │
clé publique
     ▼
SALES_ETL_SVC
```

C'est précisément le mécanisme prévu par le guide pour les utilisateurs de service.