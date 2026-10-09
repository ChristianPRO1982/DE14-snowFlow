# Compte rendu — Jour 5

# Contrôler, documenter et présenter

## État d'avancement

```text
Bloc 1 — Réponse métier finale                         ✅ TERMINÉ
Bloc 2 — Contrôle des données anormales                ⏳ À FAIRE
Bloc 3 — Consommation Snowflake                        ⏳ À FAIRE
Bloc 4 — Sécurité et droits                            ⏳ À FAIRE
Bloc 5 — Finalisation du dépôt et des livrables        ⏳ À FAIRE
Bloc 6 — Préparation de la démonstration finale        ⏳ À FAIRE
```

---

# Objectif du Jour 5

Le Jour 5 consiste à valider le pipeline construit pendant les quatre premiers jours, à produire la réponse métier attendue par la direction, à vérifier la qualité des données et la maîtrise de l'entrepôt Snowflake, puis à finaliser les livrables et préparer la démonstration.

Les objectifs sont :

```text
- répondre à la question métier à partir des MARTS ;
- comparer les anomalies détectées avec MART_DATA_QUALITY ;
- mesurer la consommation de crédits Snowflake ;
- vérifier les droits du rôle des outils ;
- finaliser le README, les captures et les documents ;
- préparer une démonstration technique reproductible.
```

---

# Bloc 1 — Réponse métier finale ✅

## 1. Question métier

La question posée par la direction d'Hudson Cab Partners est :

> Où et quand la demande de taxis jaunes est-elle la plus forte à New York,
> et combien rapporte un trajet selon la zone, l'heure et le mode de paiement ?

Le résultat final est documenté dans :

```text
docs/REPONSE.md
```

L'analyse repose sur les données de janvier, février et mars 2025, après application des règles de qualité du pipeline.

Volume final exploité :

```text
10 382 378 trajets valides
```

---

## 2. Analyse de la demande par zone et heure

La table utilisée est :

```text
NYC_TAXI.MARTS.MART_ZONE_HOURLY_DEMAND
```

Elle permet d'analyser la demande selon :

```text
zone de prise en charge
× heure
× type de jour
```

La requête finale est :

```sql
SELECT
    pickup_zone_name,
    pickup_borough,
    pickup_hour,
    CASE
        WHEN is_weekend THEN 'Weekend'
        ELSE 'Weekday'
    END AS day_type,
    nb_trips,
    avg_trips_per_day,
    avg_revenue_per_trip,
    revenue_per_hour_driven
FROM NYC_TAXI.MARTS.MART_ZONE_HOURLY_DEMAND
WHERE pickup_zone_name IS NOT NULL
ORDER BY avg_trips_per_day DESC
LIMIT 10;
```

Le tri utilise :

```text
avg_trips_per_day
```

plutôt que le nombre total brut de trajets, afin de comparer correctement les jours de semaine et les week-ends, qui ne sont pas présents en nombre égal sur la période.

---

## 3. Top 10 zones × heures

| Zone | Borough | Heure | Type de jour | Trajets | Moyenne trajets/jour | Revenu moyen/trajet |
|---|---|---:|---|---:|---:|---:|
| East Village | Manhattan | 0 | Weekend | 19 187 | 738.0 | $22.84 |
| East Village | Manhattan | 1 | Weekend | 18 869 | 725.7 | $22.11 |
| Midtown Center | Manhattan | 18 | Weekday | 38 170 | 596.4 | $24.98 |
| Midtown Center | Manhattan | 17 | Weekday | 36 602 | 571.9 | $30.06 |
| West Village | Manhattan | 0 | Weekend | 14 536 | 559.1 | $23.14 |
| Midtown Center | Manhattan | 20 | Weekday | 34 207 | 534.5 | $22.81 |
| West Village | Manhattan | 1 | Weekend | 13 505 | 519.4 | $22.57 |
| East Village | Manhattan | 2 | Weekend | 12 976 | 519.0 | $22.00 |
| Midtown Center | Manhattan | 19 | Weekday | 32 773 | 512.1 | $24.14 |
| Midtown Center | Manhattan | 21 | Weekday | 31 636 | 494.3 | $23.01 |

Deux comportements principaux apparaissent :

```text
week-end, nuit
→ East Village / West Village

semaine, fin de journée
→ Midtown Center
```

Le maximum observé est :

```text
East Village
Weekend
00:00
738,0 trajets par jour en moyenne
```

---

## 4. Analyse du revenu selon le mode de paiement

La table utilisée est :

```text
NYC_TAXI.MARTS.MART_DAILY_REVENUE
```

La requête finale est :

```sql
SELECT
    payment_type_label,
    SUM(nb_trips) AS nb_trips,
    ROUND(SUM(total_revenue), 2) AS total_revenue,
    ROUND(
        SUM(total_revenue) / NULLIF(SUM(nb_trips), 0),
        2
    ) AS avg_revenue_per_trip
FROM NYC_TAXI.MARTS.MART_DAILY_REVENUE
GROUP BY payment_type_label
ORDER BY nb_trips DESC;
```

Résultat :

| Mode de paiement | Trajets | Revenu total | Revenu moyen/trajet |
|---|---:|---:|---:|
| Credit card | 7 397 954 | $209 535 888.79 | $28.32 |
| Flex Fare trip | 1 767 528 | $43 034 783.81 | $24.35 |
| Cash | 1 063 448 | $25 208 170.14 | $23.70 |
| Dispute | 115 468 | $4 065 063.99 | $35.21 |
| No charge | 37 980 | $1 038 569.87 | $27.35 |

La carte bancaire représente de très loin le principal moyen de paiement observé.

---

## 5. Conclusions métier

Les trois conclusions intégrées dans `docs/REPONSE.md` sont :

1. La demande la plus forte se situe dans l'East Village les nuits de week-end : à minuit, on observe en moyenne 738 prises en charge par jour, puis 725,7 à 1 h.

2. En semaine, Midtown Center constitue l'autre principal point de forte demande, surtout entre 17 h et 21 h ; le pic est atteint à 18 h avec 596,4 trajets par jour en moyenne.

3. La carte bancaire est de très loin le principal mode de paiement avec près de 7,4 millions de trajets et un revenu moyen de 28,32 dollars par trajet, contre 23,70 dollars pour les paiements en espèces.

---

## 6. Limites de l'analyse

L'analyse porte uniquement sur :

```text
janvier 2025
février 2025
mars 2025
```

Elle utilise uniquement les trajets ayant passé les règles de qualité du pipeline.

Les résultats ne permettent donc pas à eux seuls de conclure à une saisonnalité annuelle.

Les catégories :

```text
Dispute
No charge
```

sont conservées dans les données mais ne doivent pas être interprétées comme des moyens de paiement commerciaux comparables à la carte bancaire ou aux espèces.

---

# Bilan du Bloc 1 ✅

```text
requête métier zone × heure                         ✅
top 10 demandé                                      ✅
analyse du revenu par mode de paiement              ✅
trois conclusions pour la direction                 ✅
limites documentées                                 ✅
docs/REPONSE.md créé                                 ✅
```

Le Bloc 1 du Jour 5 est terminé.

---

# Suite du Jour 5

```text
Bloc 2 — Contrôle des données anormales
Bloc 3 — Consommation Snowflake
Bloc 4 — Sécurité et droits
Bloc 5 — Finalisation du dépôt et des livrables
Bloc 6 — Préparation de la démonstration finale
```
