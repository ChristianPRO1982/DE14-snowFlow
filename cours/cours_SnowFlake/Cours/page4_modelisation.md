# Modélisation Dimensionnelle

Maîtriser les schémas en étoile, flocon et constellation

[← Retour Architecture](page3_architecture_dw.md)
[Synthèse →](page5_synthese.md)

## Concepts Fondamentaux

### 📊 Tables de Faits

**Caractéristiques :**

- Contiennent les **mesures quantifiables**
- Clés étrangères vers les dimensions
- Granularité définie (niveau de détail)
- Volume important de données
- Mises à jour fréquentes

**Exemples :** Ventes, Commandes, Transactions

### 🏷️ Tables de Dimensions

**Caractéristiques :**

- Contiennent les **attributs descriptifs**
- Clé primaire unique (surrogate key)
- Hiérarchies et niveaux
- Volume plus réduit
- Évolution lente (SCD)

**Exemples :** Clients, Produits, Temps, Géographie

### 🔑 Clés de Substitution

**Surrogate Keys :**

- Clés **artificielles** générées
- Indépendantes des données métier
- Généralement des entiers auto-incrémentés
- Permettent l'historisation
- Optimisent les jointures

**Avantages :** Performance, Stabilité, Flexibilité

### 📏 Granularité

**Niveau de détail :**

- **Fine :** Transaction individuelle
- **Moyenne :** Journalière, hebdomadaire
- **Agrégée :** Mensuelle, annuelle
- Impact sur performance et stockage
- Définit les possibilités d'analyse

**Principe :** Partir du plus fin possible

## Types de Schémas Dimensionnels

Schéma en Étoile
Schéma en Flocon
Schéma en Constellation

⭐ Schéma en Étoile - Exemple Ventes

DIM\_TEMPS

date\_id, annee, mois, jour, trimestre, jour\_semaine

DIM\_PRODUIT

produit\_id, nom, categorie, marque, prix\_unitaire

FAIT\_VENTES

**FK:** client\_id, produit\_id, temps\_id, magasin\_id
**Mesures:** quantite, montant, remise

DIM\_CLIENT

client\_id, nom, age, ville, segment

DIM\_MAGASIN

magasin\_id, nom, ville, region, surface

#### ✅ Avantages :

- Structure simple et intuitive
- Requêtes performantes (peu de jointures)
- Facile à comprendre et maintenir

#### ❌ Inconvénients :

- Redondance dans les dimensions
- Espace de stockage plus important
- Moins normalisé

❄️ Schéma en Flocon - Normalisation

DIM\_MARQUE

marque\_id, nom\_marque, pays\_origine

DIM\_CATEGORIE

categorie\_id, nom\_categorie, type

DIM\_PRODUIT

produit\_id, nom, marque\_id, categorie\_id

DIM\_TEMPS

date\_id, jour, mois\_id, annee\_id

FAIT\_VENTES

**FK:** client\_id, produit\_id, temps\_id
**Mesures:** quantite, montant

DIM\_VILLE

ville\_id, nom\_ville, region\_id

DIM\_CLIENT

client\_id, nom, ville\_id

#### ✅ Avantages :

- Économie d'espace de stockage
- Moins de redondance
- Intégrité des données renforcée

#### ❌ Inconvénients :

- Requêtes plus complexes (plus de jointures)
- Performance dégradée
- Maintenance plus complexe

🌌 Schéma en Constellation - Multi-Faits

DIM\_TEMPS

date\_id, annee, mois, jour

DIM\_PRODUIT

produit\_id, nom, categorie

DIM\_CLIENT

client\_id, nom, segment

FAIT\_VENTES

quantite, montant, remise

FAIT\_STOCK

stock\_initial, stock\_final, mouvement

FAIT\_COMMANDES

nb\_commandes, delai\_livraison

DIM\_FOURNISSEUR

fournisseur\_id, nom, pays

DIM\_ENTREPOT

entrepot\_id, nom, capacite

#### ✅ Avantages :

- Analyse multi-processus
- Réutilisation des dimensions
- Vision globale de l'entreprise

#### ❌ Inconvénients :

- Complexité de conception
- Maintenance plus difficile
- Risque d'incohérence

## Méthodologies : Kimball vs Inmon

### 🔄 Approche Kimball (Bottom-Up)

#### Principe :

- Démarrage par les **Data Marts**
- Construction incrémentale
- Modélisation dimensionnelle dès le départ
- Intégration progressive

#### Avantages :

- ROI rapide
- Complexité maîtrisée
- Flexibilité d'évolution
- Coûts réduits au démarrage

#### Inconvénients :

- Risque de silos de données
- Incohérences possibles
- Intégration plus complexe

### 🏗️ Approche Inmon (Top-Down)

#### Principe :

- Conception globale du **DW entreprise**
- Modèle normalisé (3NF)
- Data Marts alimentés par le DW
- Architecture centralisée

#### Avantages :

- Cohérence garantie
- Vision d'entreprise
- Qualité des données
- Évolutivité maîtrisée

#### Inconvénients :

- Investissement initial élevé
- Temps de développement long
- Complexité technique
- ROI différé

### 📊 Comparaison Détaillée

| Critère | Kimball (Bottom-Up) | Inmon (Top-Down) |
| --- | --- | --- |
| **Approche** | Data Marts → DW | DW → Data Marts |
| **Modélisation** | Dimensionnelle (étoile) | Normalisée (3NF) |
| **Temps de mise en œuvre** | Court (3-6 mois) | Long (1-3 ans) |
| **Coût initial** | Faible | Élevé |
| **Complexité** | Modérée | Élevée |
| **Performance requêtes** | Excellente | Variable |
| **Évolutivité** | Moyenne | Excellente |
| **Cohérence** | Risquée | Garantie |

## Constructeur de Schéma Interactif

+ Ajouter Table de Faits
+ Ajouter Dimension
🗑️ Effacer
💾 Sauvegarder

🎨 Glissez et construisez votre schéma dimensionnel !
Commencez par ajouter une table de faits...

## Quiz de Validation

Quel type de schéma offre les meilleures performances pour les requêtes analytiques ?

Schéma en flocon
Schéma en étoile
Schéma normalisé 3NF
Schéma en constellation