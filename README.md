# CFNEWS MCP Server

Serveur MCP (Model Context Protocol) pour l'API CFNEWS, permettant d'interroger la base de données des opérations de corporate finance, fonds d'investissement, sociétés et acteurs du marché français.

## 🚀 Installation

### Prérequis
- Python 3.10+
- Une clé API CFNEWS valide

### Installation des dépendances

```bash
pip install -r requirements.txt
```

### Configuration

1. Copiez le fichier `.env.example` vers `.env`:
```bash
cp .env.example .env
```

2. Éditez `.env` et ajoutez votre clé API CFNEWS:
```
CFNEWS_API_KEY=votre_cle_api_ici
```

## 🎯 Utilisation

### Mode Local (stdio)

Pour utiliser le serveur MCP en local avec Claude Desktop:

```bash
python server.py
```

### Configuration Claude Desktop

Ajoutez dans votre fichier de configuration Claude Desktop (`claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "cfnews": {
      "command": "python",
      "args": ["/chemin/vers/cfnews-mcp/server.py"],
      "env": {
        "CFNEWS_API_KEY": "votre_cle_api"
      }
    }
  }
}
```

### Déploiement Serveur (pour Dust)

#### Option 1: Déploiement avec FastMCP Server

```bash
# Lancer le serveur HTTP
fastmcp run server.py --port 8000 --host 0.0.0.0
```

#### Option 2: Déploiement avec uvicorn

Créez un fichier `run_server.py`:

```python
import uvicorn
from server import mcp

if __name__ == "__main__":
    uvicorn.run(
        mcp.get_asgi_app(),
        host="0.0.0.0",
        port=8000
    )
```

Puis lancez:
```bash
python run_server.py
```

#### Option 3: Déploiement Docker

Créez un `Dockerfile`:

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV CFNEWS_API_KEY=""
ENV PORT=8000

EXPOSE 8000

CMD ["python", "run_server.py"]
```

Build et run:
```bash
docker build -t cfnews-mcp .
docker run -p 8000:8000 -e CFNEWS_API_KEY=votre_cle cfnews-mcp
```

### Configuration pour Dust

Dans Dust, ajoutez un serveur MCP avec l'URL de votre serveur déployé:

```
http://votre-serveur:8000
```

Ou si déployé localement avec tunnel (ex: ngrok):
```
https://votre-tunnel.ngrok.io
```

## 🛠️ Outils Disponibles

Le serveur MCP expose les outils suivants:

### 1. `search_operations`
Recherche des opérations (LBO, M&A, levées de fonds, etc.)

**Paramètres:**
- `company_name`: Nom de la société cible
- `operation_types`: Types d'opérations (LBO, Capital Développement, M&A Corporate, etc.)
- `sectors`: Secteurs d'activité
- `date_from`, `date_to`: Période (format DD/MM/YYYY)
- `amount_min`, `amount_max`: Fourchette de montant en M€

**Exemple:**
```python
search_operations(
    operation_types=["LBO", "Capital Développement"],
    sectors=["Biotechnologies"],
    date_from="01/01/2024",
    date_to="31/12/2024"
)
```

### 2. `search_funds`
Recherche de véhicules d'investissement (fonds)

**Paramètres:**
- `fund_name`: Nom du fonds
- `management_company`: Société de gestion
- `fund_types`: Types (FCPR, FPCI, etc.)
- `segments`: Segments (LBO, VC, etc.)
- `status`: Statuts (Closé, En cours de levée, etc.)

**Exemple:**
```python
search_funds(
    segments=["Capital innovation / VC"],
    status=["En cours de levée"],
    amount_raised_min=50
)
```

### 3. `search_actors`
Recherche d'acteurs du corporate finance

**Paramètres:**
- `actor_name`: Nom de l'acteur
- `actor_types`: Types (Fonds d'investissement, Avocats, Banquiers, etc.)
- `nationalities`: Codes pays (FR, US, GB, etc.)
- `regions`: Régions françaises
- `is_tech_fund`: Filtre fonds TECH

**Exemple:**
```python
search_actors(
    actor_types=["Fonds d'investissement"],
    regions=["Île-de-France"],
    is_tech_fund=True
)
```

### 4. `search_companies`
Recherche de sociétés

**Paramètres:**
- `company_name`: Nom de la société
- `company_types`: Types (Familiale, Sté sous LBO, etc.)
- `sectors`: Secteurs d'activité
- `revenue_min`, `revenue_max`: Fourchette de CA en M€
- `is_tech`: Filtre entreprises TECH

**Exemple:**
```python
search_companies(
    sectors=["Logiciel et services informatiques"],
    revenue_min=10,
    revenue_max=100,
    is_tech=True
)
```

### 5. `search_people`
Recherche de personnalités

**Paramètres:**
- `name`: Nom ou prénom
- `organization`: Organisation actuelle
- `titles`: Titres/fonctions
- `executives_only`: Filtre cadres dirigeants
- `with_email`: Filtre avec email

**Exemple:**
```python
search_people(
    organization_types=["Fonds"],
    executives_only=True,
    regions=["Île-de-France"]
)
```

### 6. `search_news`
Recherche d'actualités CFNEWS

**Paramètres:**
- `title`: Mots dans le titre
- `themes`: Thèmes (LBO, M&A, etc.)
- `keywords`: Mots-clés
- `date_from`, `date_to`: Période de publication

**Exemple:**
```python
search_news(
    themes=["LBO", "Levée de Fonds"],
    keywords=["fintech"],
    date_from="2024-01-01"
)
```

### 7. `get_fund_portfolio`
Récupère le portefeuille d'un fonds

**Paramètres:**
- `fund_id`: ID du fonds
- `portfolio_type`: "current" (actuel) ou "exits" (sorties)

**Exemple:**
```python
get_fund_portfolio(
    fund_id=1625,
    portfolio_type="current"
)
```

## 📊 Types d'Opérations

Valeurs acceptées pour `operation_types`:
- `LBO` (271)
- `Capital Développement` (273)
- `Capital Innovation` (274)
- `M&A Corporate` (272)
- `Financement` (29093)
- `Immobilier` (275)
- `Infrastructure` (199547)
- `Restructuration` (14447)
- `Bourse` (25006)

## 🏢 Secteurs d'Activité

Secteurs principaux:
- `Biotechnologies` (124)
- `Corporate Finance` (19486)
- `Services Financiers` (305)
- `Logiciel et services informatiques` (297)
- `Internet & ecommerce, eservices` (296)
- `Santé, beauté et services associés` (302)

## 🌍 Régions Françaises

Codes régions:
- `Île-de-France` (132336)
- `Auvergne-Rhône-Alpes` (132360)
- `Occitanie` (132354)
- `Grand Est` (132334)
- `Hauts-de-France` (132355)

## 🔒 Sécurité

- Ne commitez **jamais** votre fichier `.env` avec la clé API
- Utilisez des variables d'environnement pour la clé API en production
- Limitez l'accès au serveur avec un reverse proxy (nginx, traefik)
- Activez HTTPS pour les déploiements en production

## 📝 Logs et Monitoring

Pour activer les logs détaillés:

```bash
export FASTMCP_LOG_LEVEL=DEBUG
python server.py
```

## 🐛 Dépannage

### Erreur "CFNEWS_API_KEY non définie"
- Vérifiez que le fichier `.env` existe et contient la clé
- Si en production, vérifiez les variables d'environnement du serveur

### Erreur de connexion à l'API
- Vérifiez la validité de votre clé API
- Vérifiez votre connexion internet
- Consultez les limites de votre abonnement CFNEWS

### Timeout des requêtes
- Augmentez le timeout dans `cfnews_client.py` (paramètre `timeout`)
- Réduisez le nombre de résultats avec `max_results`

## 📚 Documentation API CFNEWS

Pour plus de détails sur l'API CFNEWS, consultez la documentation officielle fournie dans `Documentation_API_CFNEWS_V1_3_9.txt`.

## 🤝 Support

Pour toute question ou problème:
1. Vérifiez la documentation de FastMCP: https://gofastmcp.com
2. Consultez la documentation CFNEWS
3. Ouvrez une issue sur le repository

## 📄 Licence

Ce projet est fourni tel quel. Assurez-vous de respecter les conditions d'utilisation de l'API CFNEWS.
