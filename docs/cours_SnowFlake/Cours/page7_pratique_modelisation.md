# Après-midi Pratique - Modélisation

Ateliers pratiques et exercices de modélisation dimensionnelle

⏰ 13h30-16h30 (3h) - Pratique intensive

[← Retour Programme](page1_intro_datawarehouse.md)
[🏠 Retour Accueil](page1_intro_datawarehouse.md)

## 📅 Planning de l'Après-midi

13h30-15h00

🎯 Atelier de Modélisation

- Exercice pratique : analyse d'un cas métier
- Identification des faits et dimensions
- Création des schémas logiques
- Travail en équipe et discussion

15h00-15h15

☕ Pause

- Pause café et détente
- Échanges informels
- Questions/réponses

15h15-16h30

🛠️ Outillage de Modélisation

- Présentation des outils (ERwin, PowerDesigner, outils libres)
- Réalisation des modèles conceptuels et logiques
- Documentation des modèles
- Bonnes pratiques et méthodologie

## 🛒 Cas d'Étude : Plateforme E-commerce "TechnoShop"

📋 Contexte Métier

**TechnoShop** est une plateforme e-commerce spécialisée dans la vente de produits technologiques.
L'entreprise souhaite créer un Data Warehouse avec **Microsoft Azure** pour analyser :

- 📊 **Performances des ventes** par produit, catégorie, période
- 👥 **Comportement clients** et segmentation
- 🌍 **Analyse géographique** des ventes
- 📈 **Évolution temporelle** des tendances
- 🏪 **Performance des fournisseurs**

☁️ Architecture Azure Proposée

**🏗️ Stack Technologique :**

- **Sources :** SQL Server (OLTP) + Fichiers CSV + APIs
- **Ingestion :** Azure Data Factory
- **Staging :** Azure Data Lake Storage Gen2
- **DW :** Azure Synapse Analytics (Pool SQL dédié)
- **BI :** Power BI + Azure Analysis Services

💾 Sources de Données Disponibles

Voici les principales tables du système transactionnel OLTP :

🛒 COMMANDES

- commande\_id INT (PK)
- client\_id INT (FK)
- date\_commande DATETIME
- statut VARCHAR(20)
- montant\_total DECIMAL(10,2)
- frais\_livraison DECIMAL(8,2)
- code\_promo VARCHAR(20)

📦 LIGNES\_COMMANDE

- ligne\_id INT (PK)
- commande\_id INT (FK)
- produit\_id INT (FK)
- quantite INT
- prix\_unitaire DECIMAL(8,2)
- remise\_pct DECIMAL(5,2)

👥 CLIENTS

- client\_id INT (PK)
- nom VARCHAR(100)
- email VARCHAR(150)
- date\_naissance DATE
- sexe CHAR(1)
- ville VARCHAR(50)
- code\_postal VARCHAR(10)
- pays VARCHAR(50)
- date\_inscription DATE

📱 PRODUITS

- produit\_id INT (PK)
- nom\_produit VARCHAR(200)
- marque VARCHAR(50)
- categorie\_id INT (FK)
- prix\_actuel DECIMAL(8,2)
- poids DECIMAL(6,3)
- fournisseur\_id INT (FK)
- date\_ajout DATE

🏷️ CATEGORIES

- categorie\_id INT (PK)
- nom\_categorie VARCHAR(100)
- categorie\_parent\_id INT (FK)
- description TEXT

🏭 FOURNISSEURS

- fournisseur\_id INT (PK)
- nom\_fournisseur VARCHAR(100)
- pays\_origine VARCHAR(50)
- note\_qualite DECIMAL(3,2)
- delai\_livraison\_moyen INT

📊 DONNEES\_EXTERNES

- date\_ref DATE (PK)
- taux\_change\_eur\_usd DECIMAL(6,4)
- indice\_confiance\_consommateur DECIMAL(5,2)
- nb\_jours\_feries INT
- evenement\_special VARCHAR(100)
- source VARCHAR(50)

🌐 SESSIONS\_WEB

- session\_id VARCHAR(50) (PK)
- client\_id INT (FK)
- date\_debut DATETIME
- duree\_session INT (secondes)
- pages\_vues INT
- source\_trafic VARCHAR(50)
- device\_type VARCHAR(20)
- a\_commande BOOLEAN

🔄 Flux de Données avec Azure

**📊 SOURCES**
SQL Server OLTP
CSV Files
APIs Externes
Logs Web

→

**🏭 ADF**
Data Factory
Pipelines ETL
Triggers
Monitoring

→

**🏞️ ADLS Gen2**
Data Lake
Raw/Staging
Partitioning
Delta Format

→

**🏢 SYNAPSE**
SQL Pool
Star Schema
Columnstore
Partitions

→

**📈 POWER BI**
Dashboards
Reports
Real-time
Mobile

## 🎯 Espace de Travail Interactif

1️⃣ Analyse
2️⃣ Modélisation
3️⃣ Validation

### 🔍 Étape 1 : Identification Faits vs Dimensions

📋 Éléments à Classer

Quantité vendue

Prix unitaire

Informations client

Détails produit

Date de commande

Montant total

Remise appliquée

Fournisseur

Catégorie produit

Localisation

Durée session web

Pages vues

Type de device

Source de trafic

Données externes

Taux de change

📊 Tables de Faits

Glissez ici les **mesures quantifiables**
(métriques, valeurs numériques)

🏷️ Tables de Dimensions

Glissez ici les **attributs descriptifs**
(contexte, catégorisations, hiérarchies)

### ⭐ Étape 2 : Construction du Schéma en Étoile

🎨 **Canvas de Modélisation**

Utilisez les boutons ci-dessous pour ajouter des tables

Glissez-déplacez pour organiser votre schéma

➕ Ajouter Table de Faits

➕ Ajouter Dimension

🗑️ Effacer

### ✅ Étape 3 : Validation du Modèle

#### 🎯 Checklist de Validation

**Table de faits identifiée**
Une table centrale avec les mesures

**Dimensions principales**
Client, Produit, Temps, Géographie

**Granularité définie**
Niveau de détail approprié

**Clés de substitution**
Surrogate keys pour l'historisation

**Hiérarchies dimensionnelles**
Niveaux d'agrégation logiques

**Cohérence métier**
Modèle répond aux besoins analytiques

🏆 Valider le Modèle

## 🛠️ Outils de Modélisation Recommandés

Azure Data Studio

🆓 Microsoft - Recommandé Azure

- Connexion native Azure Synapse
- Modélisation SQL Server/Synapse
- Extensions Data Warehouse
- Intégration Azure DevOps
- Notebooks intégrés

SQL Server Data Tools (SSDT)

🆓 Microsoft - Azure Native

- Projets Azure Synapse Analytics
- Déploiement automatisé vers Azure
- Intégration Visual Studio
- Gestion versions avec Git
- Templates Data Warehouse

ERwin Data Modeler

💼 Outil Commercial

- Support Azure Synapse Analytics
- Reverse engineering Azure SQL
- Génération scripts DDL Synapse
- Collaboration et versioning
- Intégration Power BI

PowerDesigner

💼 SAP/Sybase

- Modélisation multidimensionnelle
- Support Azure Synapse
- Architecture d'entreprise Azure
- Génération documentation
- Intégration Azure DevOps

Lucidchart / Visio

🌐 Outils Collaboratifs

- Templates Azure Architecture
- Collaboration Office 365
- Shapes Azure services
- Export vers Azure DevOps
- Intégration Teams

Azure DevOps + Git

☁️ Azure Platform

- Versioning des modèles
- CI/CD pour déploiements
- Work items pour suivi
- Intégration native Azure
- Collaboration équipe