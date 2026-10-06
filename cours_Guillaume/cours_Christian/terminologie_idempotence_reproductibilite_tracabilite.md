# Fiabilité des traitements : idempotence, reproductibilité et traçabilité

Ces trois notions sont proches, mais elles ne répondent pas au même problème.

Elles sont importantes dans les pipelines de données, les API, les systèmes distribués, les traitements batch et plus généralement dans tout système que l'on veut pouvoir **rejouer, comprendre et auditer**.

---

# 1. Idempotence

## Définition

Une opération est **idempotente** lorsqu'on peut l'exécuter plusieurs fois avec les mêmes paramètres sans modifier davantage l'état final après la première exécution.

Mathématiquement, l'idée peut être représentée ainsi :

```text
f(f(x)) = f(x)
```

Autrement dit :

```text
1 exécution
→ état A

10 exécutions identiques
→ toujours état A
```

L'idempotence est donc une **propriété recherchée d'un traitement**, et non une technologie particulière.

---

## Exemple simple

Supposons que l'on veuille définir le statut d'une commande :

```sql
UPDATE orders
SET status = 'PAID'
WHERE order_id = 42;
```

Exécuter cette requête une fois ou dix fois produit le même résultat :

```text
order_id = 42
status   = PAID
```

Cette opération est idempotente.

En revanche :

```sql
UPDATE accounts
SET balance = balance + 100
WHERE account_id = 42;
```

ne l'est pas.

Une exécution :

```text
1000 → 1100
```

Deux exécutions :

```text
1000 → 1100 → 1200
```

Le résultat dépend donc du nombre d'exécutions.

---

## Pourquoi rechercher l'idempotence ?

Dans un système réel, une opération peut être rejouée pour de nombreuses raisons :

- timeout réseau ;
- crash d'un service ;
- redémarrage d'un orchestrateur ;
- retry automatique ;
- erreur humaine ;
- reprise après incident ;
- réexécution volontaire d'un traitement historique.

Sans idempotence, un retry peut créer :

- des doublons ;
- des doubles facturations ;
- des compteurs incorrects ;
- des données incohérentes.

L'idempotence permet donc de rendre les **retries beaucoup plus sûrs**.

---

## Idempotence et mécanismes techniques

L'idempotence est une philosophie de conception.

Les technologies fournissent ensuite différents mécanismes permettant de l'implémenter.

Par exemple :

```text
INSERT ... ON CONFLICT
MERGE
UPSERT
clé unique
DELETE + INSERT contrôlé
checkpoint
historique d'exécution
message_id unique
idempotency key
version d'objet
```

Un fournisseur peut également proposer des options comme :

```text
OVERWRITE = FALSE
FORCE = FALSE
```

Mais ces options ne sont pas « l'idempotence ».

Ce sont seulement des **briques permettant au développeur de construire un traitement idempotent**.

---

## Idempotence à plusieurs niveaux

Un système peut être idempotent à un niveau mais pas à un autre.

Exemple :

```text
Fichier
  ↓
Chargement
  ↓
Table
```

On peut empêcher :

```text
même fichier
→ chargé deux fois
```

sans pour autant empêcher :

```text
fichier_v1.csv
fichier_v2.csv

→ contenant en partie les mêmes données
→ doublons métier possibles
```

Il faut donc toujours préciser :

> Idempotent par rapport à quoi ?

Cela peut être :

- un fichier ;
- une requête ;
- une ligne métier ;
- un événement ;
- un mois de données ;
- un identifiant de transaction.

---

# 2. Reproductibilité

## Définition

La **reproductibilité** est la capacité à reconstruire ultérieurement un résultat à partir des mêmes entrées, du même code et des mêmes règles.

On cherche à pouvoir dire :

```text
Entrées A
+ code version X
+ configuration Y
+ environnement Z

→ résultat R
```

et plusieurs mois plus tard :

```text
Entrées A
+ code version X
+ configuration Y
+ environnement Z

→ résultat R
```

---

## Reproductibilité et idempotence sont différentes

Une opération peut être idempotente sans être reproductible.

Exemple :

```text
GET https://example.com/data.csv
```

Le traitement peut éviter de charger deux fois le fichier.

Mais si le fournisseur modifie le contenu de :

```text
data.csv
```

tout en conservant la même URL et le même nom, il devient impossible de garantir que l'on dispose encore des données utilisées lors du premier traitement.

Le pipeline était éventuellement idempotent.

Il n'était pas nécessairement reproductible.

---

## Ce qu'il faut conserver pour reproduire un traitement

### Les données source

Il faut pouvoir identifier précisément les données utilisées.

Par exemple :

```text
customers_2026-10-06.csv
```

Mais le nom seul n'est pas toujours suffisant.

On peut conserver un hash :

```text
SHA256:
3f7d...
```

Deux fichiers ayant le même nom mais un contenu différent auront normalement deux hashes différents.

---

### Le code

Il faut connaître la version exacte du programme ayant produit le résultat.

Git permet par exemple de conserver :

```text
commit:
8a3fdd92...
```

On peut alors retrouver exactement :

- le code Python ;
- les requêtes SQL ;
- les règles métier ;
- les transformations.

---

### Les dépendances

Ce code :

```python
import pandas
```

peut avoir un comportement différent avec :

```text
pandas 2.2
```

et :

```text
pandas 3.0
```

Il peut donc être nécessaire de fixer les versions :

```text
Python 3.12
pandas 2.2.3
pyarrow 18.1.0
```

Des outils comme Docker facilitent fortement cette reproductibilité.

---

### La configuration

Une transformation peut dépendre de paramètres :

```text
threshold = 10
```

puis être modifiée plus tard :

```text
threshold = 20
```

Le code peut être identique mais le résultat différent.

Il faut donc aussi conserver :

- paramètres ;
- variables ;
- règles métier ;
- configuration utilisée.

---

## Reproductibilité et déterminisme

Une autre notion proche est le **déterminisme**.

Un traitement déterministe produit toujours le même résultat pour les mêmes entrées.

Par exemple :

```python
result = value * 2
```

est déterministe.

Alors que :

```python
result = random.random()
```

ne l'est pas nécessairement.

De même :

```sql
CURRENT_TIMESTAMP()
```

produit une valeur différente à chaque exécution.

Un pipeline reproductible peut donc nécessiter de contrôler :

- les dates ;
- les seeds aléatoires ;
- les versions ;
- les appels à des API externes ;
- les données sources.

---

# 3. Traçabilité

## Définition

La **traçabilité** consiste à pouvoir expliquer ce qui s'est passé.

Elle répond notamment aux questions :

```text
Quoi ?
Quand ?
Par qui ?
Avec quelles données ?
Avec quel code ?
Avec quels paramètres ?
Quel résultat ?
```

---

## Exemple

Un traitement peut enregistrer :

```text
execution_id   = 9821
pipeline       = monthly_sales
started_at     = 2026-10-06 08:32:14
finished_at    = 2026-10-06 08:35:02
source_file    = sales_2026-09.parquet
source_hash    = SHA256:abc123...
git_commit     = 82fd44a
rows_read      = 1 230 441
rows_written   = 1 229 987
status         = SUCCESS
```

Plusieurs mois plus tard, cette information permet de comprendre précisément ce qui a été exécuté.

---

## Logs

Les logs constituent une première forme de traçabilité :

```text
2026-10-06 08:32:14 - Download started
2026-10-06 08:32:20 - File downloaded
2026-10-06 08:32:23 - 1 230 441 rows detected
2026-10-06 08:34:58 - 1 229 987 rows inserted
2026-10-06 08:35:02 - Pipeline succeeded
```

Mais la traçabilité ne doit pas nécessairement reposer uniquement sur des logs texte.

Des informations structurées peuvent également être conservées dans des tables d'audit.

---

## Tables d'audit

Exemple :

```sql
CREATE TABLE pipeline_runs (
    run_id VARCHAR,
    pipeline_name VARCHAR,
    source_file VARCHAR,
    source_hash VARCHAR,
    started_at TIMESTAMP,
    finished_at TIMESTAMP,
    rows_read INTEGER,
    rows_written INTEGER,
    status VARCHAR
);
```

Cela permet ensuite des requêtes telles que :

```sql
SELECT *
FROM pipeline_runs
WHERE status = 'FAILED';
```

---

## Data Lineage

Dans un système de données, la traçabilité peut aller jusqu'à la **data lineage**.

Elle décrit le chemin d'une donnée :

```text
API externe
    ↓
RAW.CUSTOMERS
    ↓
STAGING.CUSTOMERS
    ↓
INTERMEDIATE.CUSTOMERS_VALID
    ↓
MART.CUSTOMER_STATS
    ↓
dashboard
```

On peut alors répondre à une question comme :

> D'où vient cette valeur affichée dans ce dashboard ?

---

# 4. Relation entre les trois notions

Ces propriétés sont complémentaires.

```text
                PIPELINE FIABLE
                      │
          ┌───────────┼───────────┐
          │           │           │
          ▼           ▼           ▼
     Idempotence Reproductibilité Traçabilité
```

## Idempotence

Répond à :

> Que se passe-t-il si je rejoue le traitement ?

Objectif :

```text
pas d'effet indésirable supplémentaire
```

---

## Reproductibilité

Répond à :

> Puis-je reconstruire exactement ce résultat plus tard ?

Objectif :

```text
mêmes entrées
+ même code
+ même configuration
→ même résultat
```

---

## Traçabilité

Répond à :

> Puis-je expliquer comment ce résultat a été obtenu ?

Objectif :

```text
historique compréhensible et auditable
```

---

# 5. Exemple global

Imaginons un traitement quotidien :

```text
transactions.csv
       ↓
pipeline
       ↓
transactions_clean
```

## Idempotence

On rejoue le traitement trois fois :

```text
100 000 lignes
→ 100 000 lignes
→ 100 000 lignes
```

et non :

```text
100 000
→ 200 000
→ 300 000
```

---

## Reproductibilité

On conserve :

```text
transactions.csv
SHA256: abc123

Git commit:
7f82acd

Docker image:
my-pipeline:1.4.2

configuration:
rules_v3.yaml
```

Six mois plus tard, on peut reconstruire le même traitement.

---

## Traçabilité

On sait que :

```text
run_id       = 1298
date         = 2026-10-06
source       = transactions.csv
hash         = abc123
rows_input   = 100000
rows_output  = 99872
rejected     = 128
status       = SUCCESS
```

On peut expliquer précisément ce qui s'est produit.

---

# 6. Une politique d'entreprise au-dessus des outils

Une technologie ne définit généralement pas à elle seule la politique de gestion des données.

Elle fournit des briques :

```text
UPSERT
MERGE
versioning
transaction
checkpoint
overwrite
retry
historique
hash
```

L'entreprise doit décider comment les utiliser.

Par exemple :

```text
MODE NORMAL
───────────
fichier déjà traité
→ ne rien faire

nouveau fichier
→ charger

échec technique
→ retry
```

Mais également prévoir les situations exceptionnelles :

```text
MODE CORRECTION
───────────────
source erronée détectée
→ identifier l'exécution concernée
→ conserver la trace de l'ancienne version
→ fournir une nouvelle version
→ recalculer les données
→ effectuer les contrôles
→ conserver la trace de la correction
```

Un système robuste ne cherche donc pas uniquement à empêcher les erreurs.

Il cherche également à permettre une **correction contrôlée des erreurs**.

---

# 7. Notions complémentaires

## Retry

Un `retry` consiste simplement à réessayer une opération ayant échoué.

```text
tentative 1 → erreur réseau
tentative 2 → succès
```

L'idempotence rend les retries beaucoup plus sûrs.

---

## Déduplication

La déduplication cherche à identifier plusieurs données représentant le même objet métier.

```text
transaction_id = 123
transaction_id = 123
```

Elle n'est pas équivalente à l'idempotence.

Un mécanisme peut empêcher le rechargement d'un fichier tout en laissant passer des doublons provenant de deux fichiers différents.

---

## Versionnement

Le versionnement permet de distinguer plusieurs états d'une même ressource :

```text
customers_v1.csv
customers_v2.csv
customers_v3.csv
```

ou :

```text
dataset_id = customers
version    = 3
```

Il facilite fortement la reproductibilité et l'audit.

---

## Hash / checksum

Un hash permet d'identifier le contenu d'un fichier :

```text
SHA256(file)
```

Ainsi :

```text
même nom + même hash
≈ même contenu

même nom + hash différent
= contenu différent
```

Il est particulièrement utile pour la traçabilité des sources.

---

# 8. Résumé

| Notion | Question principale | Exemple |
|---|---|---|
| **Idempotence** | Puis-je rejouer sans créer d'effet supplémentaire ? | Rejouer un import sans doubler les lignes |
| **Reproductibilité** | Puis-je reconstruire le même résultat plus tard ? | Conserver source, code, dépendances et configuration |
| **Traçabilité** | Puis-je expliquer ce qui s'est passé ? | Logs, audit, hash, timestamps, lineage |
| **Déduplication** | Deux éléments représentent-ils la même donnée métier ? | Deux transactions avec le même identifiant |
| **Retry** | Puis-je réessayer après une erreur ? | Relancer après un timeout réseau |
| **Versionnement** | Quelle version exacte ai-je utilisée ? | Dataset v2, commit Git précis |
| **Hash** | Le contenu est-il exactement le même ? | SHA-256 d'un fichier |

La philosophie générale peut se résumer ainsi :

```text
Idempotence
→ rendre le rejeu sûr

Reproductibilité
→ rendre le passé reconstruisible

Traçabilité
→ rendre le passé explicable
```

> ***Un pipeline réellement robuste cherche généralement à réunir les trois.***
