# Technologies Cloud pour Data Warehouse

Comparaison des solutions Azure, AWS et Google Cloud Platform

[← Retour Synthèse](page5_synthese.md)
[🏠 Retour Accueil](page1_intro_datawarehouse.md)

## 🌥️ Principaux Fournisseurs Cloud

☁️

Microsoft Azure

Plateforme cloud d'entreprise

🏢 Data Warehouse

Azure Synapse Analytics
Azure SQL Data Warehouse
Microsoft Fabric

📊 Stockage & ETL

Azure Data Lake Storage
Azure Data Factory
Azure Databricks

📈 Analytics & BI

Power BI
Azure Analysis Services
Azure Machine Learning

🚀

Amazon Web Services

Leader du marché cloud

🏢 Data Warehouse

Amazon Redshift
Amazon Redshift Spectrum
AWS Lake Formation

📊 Stockage & ETL

Amazon S3
AWS Glue
Amazon EMR

📈 Analytics & BI

Amazon QuickSight
Amazon Athena
Amazon SageMaker

🔵

Google Cloud Platform

Innovation & Big Data

🏢 Data Warehouse

BigQuery
BigQuery ML
Cloud SQL

📊 Stockage & ETL

Cloud Storage
Cloud Dataflow
Cloud Dataproc

📈 Analytics & BI

Looker
Data Studio
Cloud AI Platform

## 🏗️ Architectures par Fournisseur

Azure
AWS
GCP

### Architecture Microsoft Azure

#### 📥 INGESTION

Event Hubs
IoT Hub
Logic Apps

→

#### ⚙️ PROCESSING

Data Factory
Databricks
Stream Analytics

→

#### 💿 STORAGE

Synapse Analytics
Data Lake Storage
CosmosDB

→

#### 📊 ANALYTICS

Power BI
Analysis Services
ML Studio

**Points forts :** Intégration native Office 365, écosystème Microsoft complet, Microsoft Fabric unifié

### Architecture Amazon Web Services

#### 📥 INGESTION

Kinesis
MSK (Kafka)
Database Migration

→

#### ⚙️ PROCESSING

Glue
EMR
Lambda

→

#### 💿 STORAGE

Redshift
S3
DynamoDB

→

#### 📊 ANALYTICS

QuickSight
Athena
SageMaker

**Points forts :** Écosystème le plus mature, services très spécialisés, communauté importante

### Architecture Google Cloud Platform

#### 📥 INGESTION

Pub/Sub
Cloud Functions
Transfer Service

→

#### ⚙️ PROCESSING

Dataflow
Dataproc
Cloud Run

→

#### 💿 STORAGE

BigQuery
Cloud Storage
Firestore

→

#### 📊 ANALYTICS

Looker
Data Studio
AI Platform

**Points forts :** BigQuery serverless, expertise IA/ML native, innovation technologique

## ⚖️ Comparaison Détaillée

| Critère | Microsoft Azure | Amazon AWS | Google Cloud |
| --- | --- | --- | --- |
| **Data Warehouse Principal** | Azure Synapse Analytics Anciennement SQL DW | Amazon Redshift Colonnes + Redshift Spectrum | BigQuery Serverless, SQL standard |
| **Modèle de Tarification** | DWU (Data Warehouse Units) 💰 Pause possible | Nœuds + stockage séparé 💰 Reserved instances | À la requête + stockage 💰 Pas de serveur à gérer |
| **Scalabilité** | Scaling manuel/auto Séparation calcul/stockage | Scaling manuel Resize cluster requis | Auto-scaling complet Pas de limite théorique |
| **ETL/ELT Natif** | Azure Data Factory SSIS dans le cloud | AWS Glue Serverless Spark | Cloud Dataflow Apache Beam |
| **BI/Visualisation** | Power BI Intégration Office 365 | QuickSight ML-powered insights | Looker + Data Studio Google Workspace |
| **Machine Learning** | Azure ML Studio Cognitive Services | SageMaker Écosystème IA complet | AI Platform TensorFlow natif |
| **Sécurité & Compliance** | Azure AD intégré Certifications enterprise | IAM granulaire Le plus de certifications | Google Identity Encryption by default |
| **Écosystème** | Microsoft (.NET, Office) Hybrid cloud fort | Le plus large Marketplace étendu | Open source focused Kubernetes natif |

## 💰 Modèles de Coûts

💙 Azure Synapse

- **DWU :** 100-30000 unités
- **Pause/Reprise :** Économies importantes
- **Stockage :** Séparé, optimisé
- **Exemple :** DW100c ~900€/mois
- **Microsoft Fabric :** Capacité unifiée

🧡 Amazon Redshift

- **Nœuds :** dc2.large à ra3.16xlarge
- **Reserved :** -75% sur 3 ans
- **Spectrum :** Requêtes S3 séparées
- **Exemple :** dc2.large ~180€/mois
- **Serverless :** RPU (Redshift Processing Units)

💙 Google BigQuery

- **À la demande :** $5/TB de données scannées
- **Flat-rate :** Slots garantis
- **Stockage :** $0.02/GB/mois
- **Exemple :** 100 slots ~1800€/mois
- **Pas de serveur :** Coûts opérationnels réduits

## 🎯 Matrice de Décision

🏢

Écosystème Microsoft ?

Si déjà Office 365, .NET, SQL Server → **Azure**

📊

Priorité Analytics ?

Si focus BI/ML/Big Data → **Google Cloud**

🔧

Flexibilité maximale ?

Si besoins variés/complexes → **AWS**

💰

Budget optimisé ?

Variables selon usage, BigQuery souvent plus économique

⚡

Time-to-Market ?

BigQuery serverless le plus rapide à déployer

🛡️

Compliance stricte ?

AWS a le plus de certifications sectorielles

## ✅ Meilleures Pratiques Multi-Cloud

🎯 Évaluation des Besoins

Analysez vos besoins en performance, coûts, intégration existante et compétences équipe avant de choisir.

🔒 Sécurité First

Configurez IAM/RBAC dès le départ, chiffrement end-to-end, et monitoring des accès pour tous les clouds.

💰 Optimisation Coûts

Surveillez les coûts en temps réel, utilisez les options pause/scaling, et optimisez les requêtes.

📊 Monitoring & Observabilité

Implémentez logging, métriques et alertes pour performance, disponibilité et coûts.

🔄 Backup & Disaster Recovery

Planifiez sauvegarde cross-region, tests de restauration et stratégie de continuité.

🚀 Evolution & Scalabilité

Architecturez pour la croissance, anticipez les besoins futurs et restez technologiquement agile.

## 📝 Quiz Technologies Cloud

Quel service cloud offre la meilleure approche serverless pour un Data Warehouse ?

Azure Synapse Analytics
Google BigQuery
Amazon Redshift
Snowflake sur AWS