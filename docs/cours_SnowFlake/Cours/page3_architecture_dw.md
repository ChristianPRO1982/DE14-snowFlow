# Architecture Data Warehouse

Comprendre l'architecture complète d'un entrepôt de données

[← Retour OLTP vs OLAP](page2_oltp_olap.md)
[Modélisation →](page4_modelisation.md)

## Architecture Générale d'un Data Warehouse

💾 SOURCES DE DONNÉES

Systèmes opérationnels, fichiers, APIs, données externes

⬇️

🔄 ZONE DE STAGING

Extraction et transformation temporaire des données

⬇️

🏢 DATA WAREHOUSE

Stockage intégré et historisé des données

⬇️

📊 DATA MARTS

Vues métier spécialisées par domaine

⬇️

📈 COUCHE DE PRÉSENTATION

Outils de reporting et d'analyse

### Sélectionnez une couche

Cliquez sur une couche de l'architecture pour voir les détails.

## Flux de Données Interactif

#### 📥 EXTRACT

ERP
CRM
Web

→

#### ⚙️ TRANSFORM

Nettoyage
Validation
Agrégation

→

#### 💿 LOAD

Data Warehouse
Data Marts
Dimensions

→

#### 📊 CONSUME

BI Tools
Dashboards
Reports

### Processus ETL

Cliquez sur une étape du processus pour voir les détails.

## Approches Architecturales

Centralisée
Fédérée
Distribuée
Cloud

### 🏢 Architecture Centralisée

- Un seul entrepôt de données central
- Toutes les données dans un même système
- Contrôle centralisé de la qualité
- Vision unique et cohérente
- Plus simple à maintenir

### ⚖️ Avantages / Inconvénients

**✅ Avantages :**

- Cohérence des données garantie
- Sécurité centralisée
- Coûts d'infrastructure réduits

**❌ Inconvénients :**

- Point de défaillance unique
- Scalabilité limitée
- Flexibilité réduite

### 🔗 Architecture Fédérée

- Multiples sources connectées
- Requêtes distribuées en temps réel
- Données restent dans les systèmes source
- Métadonnées centralisées
- Virtualisation des données

### ⚖️ Avantages / Inconvénients

**✅ Avantages :**

- Données toujours à jour
- Pas de duplication
- Flexibilité maximale

**❌ Inconvénients :**

- Performances variables
- Complexité technique
- Dépendance aux systèmes source

### 🌐 Architecture Distribuée

- Multiples entrepôts interconnectés
- Répartition géographique
- Synchronisation des données
- Redondance et haute disponibilité
- Scalabilité horizontale

### ⚖️ Avantages / Inconvénients

**✅ Avantages :**

- Haute disponibilité
- Performance locale optimisée
- Scalabilité excellente

**❌ Inconvénients :**

- Complexité de synchronisation
- Coûts élevés
- Maintenance complexe

### ☁️ Architecture Cloud

- Services managés (Azure, AWS, GCP)
- Élasticité automatique
- Séparation calcul/stockage
- Pay-as-you-go
- Intégration native

### ⚖️ Avantages / Inconvénients

**✅ Avantages :**

- Évolutivité instantanée
- Maintenance réduite
- Innovation continue

**❌ Inconvénients :**

- Dépendance au fournisseur
- Coûts variables
- Contraintes de conformité

## Quiz de Compréhension

Quelle couche de l'architecture est responsable du nettoyage et de la transformation des données ?

Couche de présentation
Zone de staging
Data marts
Sources de données