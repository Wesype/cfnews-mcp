# Exemples d'Utilisation du Serveur MCP CFNEWS

Ce document présente des exemples concrets d'utilisation du serveur MCP CFNEWS avec un LLM (Claude, GPT, etc.).

## Cas d'Usage 1: Analyse de Marché LBO

**Prompt pour le LLM:**
```
Analyse le marché des LBO en France en 2024 dans le secteur des biotechnologies. 
Donne-moi:
1. Le nombre total d'opérations
2. Les principaux acteurs impliqués
3. Les tendances de valorisation
```

**Outils MCP utilisés:**
```python
# 1. Rechercher les opérations LBO biotech en 2024
search_operations(
    operation_types=["LBO"],
    sectors=["Biotechnologies"],
    date_from="01/01/2024",
    date_to="31/12/2024",
    max_results=50
)

# 2. Identifier les fonds actifs
search_actors(
    actor_types=["Fonds d'investissement"],
    is_tech_fund=True,
    regions=["Île-de-France"]
)
```

## Cas d'Usage 2: Due Diligence d'un Fonds

**Prompt:**
```
Je veux analyser le fonds "Elaia Partners". 
Donne-moi:
- Ses caractéristiques principales
- Son portefeuille actuel
- Ses investissements récents
- Les sorties récentes
```

**Outils MCP utilisés:**
```python
# 1. Rechercher le fonds
search_actors(
    actor_name="Elaia",
    actor_types=["Fonds d'investissement"]
)

# 2. Une fois l'ID récupéré, obtenir le portefeuille
get_fund_portfolio(
    fund_id=12345,  # ID récupéré de l'étape 1
    portfolio_type="current"
)

# 3. Sorties du fonds
get_fund_portfolio(
    fund_id=12345,
    portfolio_type="exits"
)

# 4. Dernières opérations
search_operations(
    company_name="Elaia",
    date_from="01/01/2024"
)
```

## Cas d'Usage 3: Recherche de Coinvestisseurs

**Prompt:**
```
Trouve-moi des fonds qui investissent dans les mêmes secteurs que Bpifrance:
- Deeptech
- Cleantech
- IA
Avec un ticket moyen entre 5M€ et 50M€
```

**Outils MCP utilisés:**
```python
# 1. Rechercher des fonds tech
search_actors(
    actor_types=["Fonds d'investissement"],
    is_tech_fund=True,
    regions=["Île-de-France", "Auvergne-Rhône-Alpes"]
)

# 2. Filtrer par montants d'investissement
search_funds(
    segments=["Capital innovation / VC"],
    amount_raised_min=50,
    amount_raised_max=500
)

# 3. Voir leurs investissements récents
search_operations(
    operation_types=["Capital Innovation"],
    amount_min=5,
    amount_max=50,
    date_from="01/01/2023"
)
```

## Cas d'Usage 4: Analyse Sectorielle

**Prompt:**
```
Analyse le secteur fintech français:
- Nombre d'opérations en 2024
- Montant total levé
- Principaux investisseurs
- Startups les plus actives en levée
```

**Outils MCP utilisés:**
```python
# 1. Opérations fintech 2024
search_operations(
    date_from="01/01/2024",
    date_to="31/12/2024",
    max_results=100
)

# Puis filtrer avec keywords ou secteurs

# 2. Sociétés fintech
search_companies(
    sectors=["Services Financiers"],
    is_tech=True,
    regions=["Île-de-France"]
)

# 3. Actualités fintech
search_news(
    keywords=["fintech"],
    themes=["Levée de Fonds"],
    date_from="2024-01-01"
)

# 4. Fonds investissant dans la fintech
search_actors(
    actor_types=["Fonds d'investissement"],
    is_tech_fund=True
)
```

## Cas d'Usage 5: Cartographie des Avocats M&A

**Prompt:**
```
Liste-moi les principaux cabinets d'avocats spécialisés en M&A et private equity 
en Île-de-France avec leurs associés principaux.
```

**Outils MCP utilisés:**
```python
# 1. Rechercher les cabinets d'avocats
search_actors(
    actor_types=["Avocats"],
    regions=["Île-de-France"],
    max_results=50
)

# 2. Associés de ces cabinets
search_people(
    organization_types=["Avocats"],
    titles=["Associé(e)", "Partner"],
    executives_only=True,
    regions=["Île-de-France"],
    with_email=True
)

# 3. Opérations récentes conseillées
search_operations(
    date_from="01/01/2024",
    max_results=100
)
# Filtrer par rôle conseil
```

## Cas d'Usage 6: Tracking de Mouvements

**Prompt:**
```
Quels sont les mouvements récents de directeurs dans les fonds d'investissement 
tech en France?
```

**Outils MCP utilisés:**
```python
# 1. Rechercher les mouvements récents
search_mouvements(
    date_from="01/01/2024",
    organization_types=["Fonds"],
    max_results=50
)

# 2. Personnalités concernées
search_people(
    organization_types=["Fonds"],
    titles=["Directeur général", "Managing Partner"],
    max_results=100
)
```

## Cas d'Usage 7: Deal Sourcing

**Prompt:**
```
Je cherche des sociétés SaaS B2B en France:
- CA entre 10M€ et 50M€
- Création après 2015
- Pas encore sous LBO
- Avec un profil de croissance intéressant
```

**Outils MCP utilisés:**
```python
# 1. Rechercher des sociétés correspondantes
search_companies(
    sectors=["Logiciel et services informatiques"],
    company_types=["Indépendante", "Familiale"],
    revenue_min=10,
    revenue_max=50,
    is_tech=True,
    regions=["Île-de-France"]
)

# 2. Vérifier leurs deals passés
# Pour chaque société identifiée:
search_operations(
    company_name="NomDeLaSociété",
    date_from="01/01/2015"
)

# 3. Identifier les dirigeants
search_people(
    organization="NomDeLaSociété",
    executives_only=True,
    with_email=True
)
```

## Cas d'Usage 8: Veille Concurrentielle

**Prompt:**
```
Surveille les activités d'Ardian en France:
- Nouvelles levées de fonds
- Acquisitions récentes
- Nouveaux véhicules
- Mouvements d'équipe
```

**Outils MCP utilisés:**
```python
# 1. Actualités Ardian
search_news(
    title="Ardian",
    date_from="2024-01-01"
)

# 2. Opérations récentes
search_operations(
    company_name="Ardian",
    date_from="01/01/2024"
)

# 3. Nouveaux fonds
search_funds(
    management_company="Ardian",
    status=["En cours de levée", "Closé"]
)

# 4. Équipe
search_people(
    organization="Ardian",
    executives_only=True
)
```

## Cas d'Usage 9: Préparation de Pitch

**Prompt:**
```
Je prépare un pitch pour un fonds. Aide-moi à comprendre:
- Leur thèse d'investissement
- Leurs investissements typiques
- Leurs co-investisseurs habituels
- Leurs conseillers récurrents
```

**Outils MCP utilisés:**
```python
# 1. Profil du fonds
search_actors(
    actor_name="NomDuFonds",
    actor_types=["Fonds d'investissement"]
)

# 2. Véhicules actifs
search_funds(
    management_company="NomDuFonds",
    status=["Closé", "En cours de levée"]
)

# 3. Historique d'investissements
search_operations(
    company_name="NomDuFonds",
    date_from="01/01/2020",
    max_results=100
)

# 4. Portefeuille actuel
get_fund_portfolio(
    fund_id=12345,
    portfolio_type="current"
)
```

## Cas d'Usage 10: Analyse de Réseau

**Prompt:**
```
Cartographie le réseau autour de BNP Paribas Private Equity:
- Sociétés en portefeuille
- Partenaires de co-investissement
- Avocats et banquiers conseils
- Personnalités clés
```

**Outils MCP utilisés:**
```python
# 1. Profil BNP PE
search_actors(
    actor_name="BNP Paribas",
    actor_types=["Fonds d'investissement"]
)

# 2. Portefeuille
get_fund_portfolio(
    fund_id=1625,
    portfolio_type="current"
)

# 3. Co-investisseurs (via opérations communes)
search_operations(
    company_name="BNP Paribas",
    date_from="01/01/2020",
    max_results=200
)

# 4. Équipe
search_people(
    organization="BNP Paribas",
    organization_types=["Fonds"],
    executives_only=True
)
```

## Bonnes Pratiques

### Chainer les Requêtes

Les requêtes MCP sont plus puissantes quand elles sont chainées:

```python
# 1. D'abord identifier l'entité
results = search_actors(actor_name="Eurazeo")

# 2. Extraire l'ID du résultat
fund_id = results["items"][0]["id"]

# 3. Utiliser l'ID pour des requêtes plus précises
portfolio = get_fund_portfolio(fund_id=fund_id)
```

### Utiliser les Filtres Progressivement

Commencez large, puis affinez:

```python
# Étape 1: Large
search_operations(
    operation_types=["LBO"],
    date_from="01/01/2024"
)

# Étape 2: Plus précis
search_operations(
    operation_types=["LBO"],
    sectors=["Biotechnologies"],
    date_from="01/01/2024",
    amount_min=50
)

# Étape 3: Très spécifique
search_operations(
    operation_types=["LBO"],
    sectors=["Biotechnologies"],
    date_from="01/01/2024",
    amount_min=50,
    regions=["Île-de-France"]
)
```

### Pagination pour Analyses Complètes

Pour des analyses exhaustives:

```python
# Page 1
results_p1 = search_operations(page=1, max_results=50)

# Page 2
results_p2 = search_operations(page=2, max_results=50)

# Agréger les résultats pour analyse complète
```

## Prompts Types pour le LLM

### Prompt d'Analyse
```
Utilise les outils CFNEWS pour analyser [sujet]. 
Structure ton analyse en:
1. Vue d'ensemble quantitative
2. Acteurs principaux
3. Tendances observées
4. Insights clés
```

### Prompt de Comparaison
```
Compare [entité A] et [entité B] en utilisant CFNEWS.
Analyse:
- Leur activité respective
- Leurs segments d'intervention
- Leurs performances relatives
```

### Prompt de Veille
```
Fais une veille sur [sujet] pour la période [dates].
Identifie:
- Les événements majeurs
- Les acteurs actifs
- Les montants en jeu
```

## Limitations à Connaître

1. **Pagination**: Max 10-50 résultats par requête selon l'endpoint
2. **Rate limiting**: Respecter les limites API CFNEWS
3. **Données historiques**: Les données anciennes peuvent être incomplètes
4. **IDs**: Certaines requêtes nécessitent des IDs récupérés précédemment

## Support

Pour plus d'exemples ou des questions spécifiques, consultez:
- La documentation API CFNEWS
- Les logs du serveur MCP
- Les issues GitHub du projet
