# OLTP vs OLAP

Comprendre les différences fondamentales entre systèmes transactionnels et analytiques

[← Retour Introduction](page1_intro_datawarehouse.md)
[Architecture DW →](page3_architecture_dw.md)

## OLTP

Online Transaction Processing

- **Objectif :** Gestion des opérations quotidiennes
- **Données :** Actuelles, détaillées, normalisées
- **Utilisateurs :** Opérationnels (milliers)
- **Requêtes :** Simples, rapides, CRUD
- **Volume :** Lectures/écritures équilibrées

## OLAP

Online Analytical Processing

- **Objectif :** Analyse et aide à la décision
- **Données :** Historiques, agrégées, dénormalisées
- **Utilisateurs :** Analystes, décideurs (centaines)
- **Requêtes :** Complexes, analytiques, lecture
- **Volume :** Principalement des lectures

## Exemples Pratiques par Secteur

Banque
Commerce
Santé

### 🏧 OLTP - Système Bancaire

**Opération :** Retrait au distributeur

**Données :** Solde compte, historique transactions

**Réponse :** < 2 secondes

**Utilisateurs :** Clients (millions)

### 📊 OLAP - Analyse Bancaire

**Analyse :** Tendances de crédit par région

**Données :** 5 ans d'historique agrégé

**Réponse :** Quelques minutes

**Utilisateurs :** Analystes risque (dizaines)

### 🛒 OLTP - E-commerce

**Opération :** Commande en ligne

**Données :** Stock, prix, panier client

**Réponse :** Temps réel

**Utilisateurs :** Clients web (millions)

### 📈 OLAP - Business Intelligence

**Analyse :** Performance des ventes par produit

**Données :** Historique multi-années

**Réponse :** Rapports batch

**Utilisateurs :** Direction commerciale

### 🏥 OLTP - Dossier Patient

**Opération :** Consultation médicale

**Données :** Antécédents, prescriptions

**Réponse :** Immédiate

**Utilisateurs :** Personnel médical

### 🔬 OLAP - Épidémiologie

**Analyse :** Tendances de maladies

**Données :** Agrégations populationnelles

**Réponse :** Études longitudinales

**Utilisateurs :** Chercheurs, autorités

## Quiz de Compréhension

Quel système utiliseriez-vous pour analyser les tendances de vente des 3 dernières années ?

OLTP - Base opérationnelle
OLAP - Data Warehouse
Les deux systèmes
Aucun des deux