# Réponse à la direction d'Hudson Cab Partners

## La question

Où et quand la demande de taxis jaunes est-elle la plus forte à New York,
et combien rapporte un trajet selon la zone, l'heure et le mode de paiement ?

## Requête — demande par zone et heure

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

## Résultat — Top 10 zones × heures

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

## Requête — revenu par mode de paiement

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

## Résultat — modes de paiement

| Mode de paiement | Trajets | Revenu total | Revenu moyen/trajet |
|---|---:|---:|---:|
| Credit card | 7 397 954 | $209 535 888.79 | $28.32 |
| Flex Fare trip | 1 767 528 | $43 034 783.81 | $24.35 |
| Cash | 1 063 448 | $25 208 170.14 | $23.70 |
| Dispute | 115 468 | $4 065 063.99 | $35.21 |
| No charge | 37 980 | $1 038 569.87 | $27.35 |

## Ce qu'il faut en retenir

1. La demande la plus forte se situe dans l'East Village les nuits de week-end : à minuit, on observe en moyenne 738 prises en charge par jour, puis 725,7 à 1 h.

2. En semaine, Midtown Center constitue l'autre principal point de forte demande, surtout entre 17 h et 21 h ; le pic est atteint à 18 h avec 596,4 trajets par jour en moyenne.

3. La carte bancaire est de très loin le principal mode de paiement avec près de 7,4 millions de trajets et un revenu moyen de 28,32 dollars par trajet, contre 23,70 dollars pour les paiements en espèces.

## Limites

L'analyse porte uniquement sur les trajets Yellow Taxi de janvier à mars 2025.

Seuls les trajets ayant passé les règles de qualité du pipeline sont utilisés, soit
10 382 378 trajets valides.

Les résultats décrivent les trajets observés pendant cette période et ne permettent
pas à eux seuls de conclure à une saisonnalité annuelle.

Les catégories de paiement telles que `Dispute` et `No charge` sont conservées dans
les données mais ne doivent pas être interprétées comme des modes de paiement
commerciaux comparables à la carte bancaire ou aux espèces.
