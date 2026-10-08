Pour le **Jour 5 — Contrôler, documenter et présenter**, je te propose **6 blocs**, directement alignés sur le brief et l’évaluation. Texte collé(1)

### Bloc 1 — Répondre à la question métier
Écrire la requête SQL finale qui répond à la direction : **où et quand la demande est-elle la plus forte, et combien rapporte un trajet selon la zone, l’heure et le mode de paiement ?** On produira le Top 10 demandé puis `docs/REPONSE.md` avec la requête et trois phrases d’interprétation compréhensibles par la direction. Texte collé(1)

### Bloc 2 — Contrôler les données anormales
Compter directement dans `INT_TRIPS__FLAGGED` les trajets rejetés et leurs motifs, puis comparer ces résultats avec `MART_DATA_QUALITY`. L’objectif est de prouver que le mart de qualité reflète correctement les anomalies réellement détectées par les règles de transformation. Texte collé(1)

### Bloc 3 — Mesurer la consommation Snowflake
Examiner la consommation du warehouse `NYC_TAXI_WH` et les crédits utilisés pendant le projet. On vérifiera également que sa configuration reste conforme au brief : taille `X-Small` et suspension automatique rapide. Cette partie servira aussi de preuve lors de la démonstration finale. Texte collé(1)

### Bloc 4 — Vérifier la sécurité et les droits
Contrôler les privilèges du rôle `TRANSFORMER` et de l’utilisateur `AIRFLOW_SVC`, puis démontrer qu’ils peuvent faire leur travail sans disposer de droits excessifs. Le brief demande notamment de pouvoir montrer **un accès autorisé dans le périmètre et un accès refusé hors périmètre**. Texte collé(1)

### Bloc 5 — Finaliser les livrables et le dépôt
Faire un audit du dépôt : `README.md` reproductible, scripts Snowflake, ingestion Python, projet Astro/Airflow, contrôles SQL, `.env.example`, fiche source, `REPONSE.md`, captures et `.gitignore`. On vérifiera surtout qu’**aucun secret ni clé privée n’est versionné** et qu’un autre développeur peut comprendre puis reproduire le projet à partir du README. Texte collé(1)

### Bloc 6 — Préparer la démonstration finale
Préparer le scénario des **15 minutes de démonstration** : droits Snowflake, trois runs Airflow, graphe du DAG, replay idempotent, contrôle volontairement en échec, requête métier finale et crédits consommés. L’idée sera de construire un déroulé court et reproductible plutôt que d’improviser le jour de l’évaluation. Texte collé(1)

### Bonus — Discord / Astro hébergé
Seulement si tout le reste est terminé : notification Discord en fin d’exécution et éventuellement déploiement sur Astro hébergé. Ce sont explicitement des bonus, donc je les laisserais **après validation complète des six blocs principaux**. Texte collé(1)

On commencera donc par **Bloc 1 — la requête métier finale**, et comme d’habitude on ne développera que celui-là.