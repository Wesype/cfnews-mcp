"""Serveur MCP pour l'API CFNEWS."""
import os
from typing import Optional, Dict, Any, List
from datetime import datetime
import json

from fastmcp import FastMCP
from dotenv import load_dotenv

from utils.cfnews_client import CFNewsClient, CFNewsAPIError

# Charger les variables d'environnement
load_dotenv()

# Créer le serveur MCP
mcp = FastMCP("CFNEWS", dependencies=["httpx", "python-dotenv"])

# Client API global
client: Optional[CFNewsClient] = None


def get_client() -> CFNewsClient:
    """Récupère ou initialise le client API."""
    global client
    if client is None:
        api_key = os.getenv("CFNEWS_API_KEY")
        if not api_key:
            raise ValueError("CFNEWS_API_KEY non définie dans les variables d'environnement")
        client = CFNewsClient(api_key)
    return client


def format_response(data: Dict[str, Any], max_items: int = 10) -> str:
    """
    Formate la réponse de l'API pour le LLM.
    
    Args:
        data: Données de l'API
        max_items: Nombre maximum d'items à retourner
    """
    if "items" not in data:
        return json.dumps(data, ensure_ascii=False, indent=2)
    
    result = {
        "count": data.get("count", 0),
        "total": data.get("total", 0),
        "page": data.get("page", 1),
        "nb_pages": data.get("nb_pages", 1),
        "items": data["items"][:max_items]
    }
    
    if data.get("total", 0) > max_items:
        result["note"] = f"Affichage des {max_items} premiers résultats sur {data['total']} au total"
    
    return json.dumps(result, ensure_ascii=False, indent=2)


@mcp.tool()
async def search_operations(
    company_name: Optional[str] = None,
    operation_types: Optional[List[str]] = None,
    sectors: Optional[List[str]] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    amount_min: Optional[float] = None,
    amount_max: Optional[float] = None,
    page: int = 1,
    max_results: int = 10
) -> str:
    """
    Recherche des opérations (deals, LBO, M&A, etc.) dans la base CFNEWS.
    
    Args:
        company_name: Nom de la société cible
        operation_types: Types d'opérations (ex: ["LBO", "Capital Développement"])
        sectors: Secteurs d'activité (ex: ["Biotechnologies", "Services Financiers"])
        date_from: Date de début (format DD/MM/YYYY)
        date_to: Date de fin (format DD/MM/YYYY)
        amount_min: Montant minimum de l'opération en M€
        amount_max: Montant maximum de l'opération en M€
        page: Numéro de page
        max_results: Nombre maximum de résultats à afficher
    
    Returns:
        JSON formaté des opérations trouvées
    """
    try:
        api_client = get_client()
        
        # Construire les filtres
        filters = {}
        
        if company_name:
            filters["op_nom"] = company_name
        
        if operation_types:
            # Mapping des types d'opérations communs
            type_mapping = {
                "LBO": 271,
                "Capital Développement": 273,
                "Capital Innovation": 274,
                "M&A Corporate": 272,
                "Financement": 29093,
                "Immobilier": 275,
                "Infrastructure": 199547,
                "Restructuration": 14447,
                "Bourse": 25006
            }
            filters["op_type"] = [type_mapping.get(t, t) for t in operation_types]
        
        if sectors:
            # Mapping des secteurs communs
            sector_mapping = {
                "Biotechnologies": 124,
                "Corporate Finance": 19486,
                "Services Financiers": 305,
                "Logiciel et services informatiques": 297,
                "Internet & ecommerce, eservices": 296,
                "Santé, beauté et services associés": 302
            }
            filters["sector"] = [sector_mapping.get(s, s) for s in sectors]
        
        if date_from:
            filters["depuis"] = date_from
        
        if date_to:
            filters["jusquau"] = date_to
        
        if amount_min is not None:
            filters["Montantmin"] = amount_min
        
        if amount_max is not None:
            filters["Montantmax"] = amount_max
        
        # Effectuer la recherche
        result = await api_client.get_operations(page=page, filters=filters)
        
        return format_response(result, max_results)
    
    except CFNewsAPIError as e:
        return json.dumps({"error": str(e)}, ensure_ascii=False)
    except Exception as e:
        return json.dumps({"error": f"Erreur inattendue: {str(e)}"}, ensure_ascii=False)


@mcp.tool()
async def search_funds(
    fund_name: Optional[str] = None,
    management_company: Optional[str] = None,
    fund_types: Optional[List[str]] = None,
    segments: Optional[List[str]] = None,
    status: Optional[List[str]] = None,
    amount_raised_min: Optional[float] = None,
    amount_raised_max: Optional[float] = None,
    page: int = 1,
    max_results: int = 10
) -> str:
    """
    Recherche des véhicules d'investissement (fonds) dans CFNEWS.
    
    Args:
        fund_name: Nom du véhicule
        management_company: Société de gestion
        fund_types: Types de véhicules (ex: ["FCPR", "FPCI"])
        segments: Segments (ex: ["LBO", "Capital développement", "Venture Capital"])
        status: Statuts (ex: ["Closé", "En cours de levée"])
        amount_raised_min: Montant levé minimum en M€
        amount_raised_max: Montant levé maximum en M€
        page: Numéro de page
        max_results: Nombre maximum de résultats
    
    Returns:
        JSON formaté des fonds trouvés
    """
    try:
        api_client = get_client()
        
        filters = {}
        
        if fund_name:
            filters["vehicle_nom"] = fund_name
        
        if management_company:
            filters["vehicle_soc_nom"] = management_company
        
        if fund_types:
            filters["vehicle_type"] = fund_types
        
        if segments:
            # Mapping des segments communs
            segment_mapping = {
                "LBO": 189615,
                "Capital développement": 189607,
                "Capital innovation / VC": 189608,
                "Amorçage": 189606,
                "Dette": 189609,
                "Fonds de fonds": 189610
            }
            filters["vehicle_segment"] = [segment_mapping.get(s, s) for s in segments]
        
        if status:
            # Mapping des statuts
            status_mapping = {
                "Closé": 189639,
                "En cours de levée": 189636,
                "1er closing": 189637
            }
            filters["vehicle_status"] = [status_mapping.get(s, s) for s in status]
        
        if amount_raised_min is not None:
            filters["Montantmin"] = amount_raised_min
        
        if amount_raised_max is not None:
            filters["Montantmax"] = amount_raised_max
        
        result = await api_client.get_vehicules(page=page, filters=filters)
        
        return format_response(result, max_results)
    
    except CFNewsAPIError as e:
        return json.dumps({"error": str(e)}, ensure_ascii=False)
    except Exception as e:
        return json.dumps({"error": f"Erreur inattendue: {str(e)}"}, ensure_ascii=False)


@mcp.tool()
async def search_actors(
    actor_name: Optional[str] = None,
    actor_types: Optional[List[str]] = None,
    nationalities: Optional[List[str]] = None,
    regions: Optional[List[str]] = None,
    is_tech_fund: Optional[bool] = None,
    page: int = 1,
    max_results: int = 10
) -> str:
    """
    Recherche des acteurs du corporate finance (fonds, avocats, banquiers, conseils).
    
    Args:
        actor_name: Nom de l'acteur
        actor_types: Types d'acteurs (ex: ["Fonds d'investissement", "Avocats", "Banquiers"])
        nationalities: Nationalités (codes ISO: "FR", "US", "GB", etc.)
        regions: Régions françaises (ex: ["Île-de-France", "Auvergne-Rhône-Alpes"])
        is_tech_fund: Filtre pour les fonds TECH uniquement
        page: Numéro de page
        max_results: Nombre maximum de résultats
    
    Returns:
        JSON formaté des acteurs trouvés
    """
    try:
        api_client = get_client()
        
        filters = {}
        
        if actor_name:
            filters["acteur_nom"] = actor_name
        
        if actor_types:
            # Mapping des types d'acteurs
            type_mapping = {
                "Fonds d'investissement": 187,
                "Avocats": 188,
                "Banquiers": 189,
                "Conseils": 190,
                "Asset Managers": 451255,
                "Investisseurs institutionnels": 191
            }
            filters["acteur_domaine"] = [type_mapping.get(t, t) for t in actor_types]
        
        if nationalities:
            filters["acteur_zone"] = nationalities
        
        if regions:
            # Mapping des régions
            region_mapping = {
                "Île-de-France": 132336,
                "Auvergne-Rhône-Alpes": 132360,
                "Occitanie": 132354,
                "Grand Est": 132334,
                "Hauts-de-France": 132355
            }
            filters["acteur_region"] = [region_mapping.get(r, r) for r in regions]
        
        if is_tech_fund is not None:
            filters["uniqut_istech"] = "oui" if is_tech_fund else "non"
        
        result = await api_client.get_acteurs(page=page, filters=filters)
        
        return format_response(result, max_results)
    
    except CFNewsAPIError as e:
        return json.dumps({"error": str(e)}, ensure_ascii=False)
    except Exception as e:
        return json.dumps({"error": f"Erreur inattendue: {str(e)}"}, ensure_ascii=False)


@mcp.tool()
async def search_companies(
    company_name: Optional[str] = None,
    company_types: Optional[List[str]] = None,
    sectors: Optional[List[str]] = None,
    regions: Optional[List[str]] = None,
    revenue_min: Optional[float] = None,
    revenue_max: Optional[float] = None,
    is_tech: Optional[bool] = None,
    page: int = 1,
    max_results: int = 10
) -> str:
    """
    Recherche des sociétés dans la base CFNEWS.
    
    Args:
        company_name: Nom de la société
        company_types: Types (ex: ["Familiale", "Sté sous LBO", "Cotée"])
        sectors: Secteurs d'activité
        regions: Régions françaises
        revenue_min: CA minimum en M€
        revenue_max: CA maximum en M€
        is_tech: Filtre entreprises TECH uniquement
        page: Numéro de page
        max_results: Nombre maximum de résultats
    
    Returns:
        JSON formaté des sociétés trouvées
    """
    try:
        api_client = get_client()
        
        filters = {}
        
        if company_name:
            filters["soc_nom"] = company_name
        
        if company_types:
            type_mapping = {
                "Familiale": 260,
                "Sté sous LBO": 20104,
                "Cotée": 18904,
                "Indépendante": 259
            }
            filters["soc_activity"] = [type_mapping.get(t, t) for t in company_types]
        
        if sectors:
            sector_mapping = {
                "Biotechnologies": 124,
                "Services Financiers": 305,
                "Logiciel et services informatiques": 297
            }
            filters["sector"] = [sector_mapping.get(s, s) for s in sectors]
        
        if regions:
            region_mapping = {
                "Île-de-France": 132336,
                "Auvergne-Rhône-Alpes": 132360
            }
            filters["soc_region"] = [region_mapping.get(r, r) for r in regions]
        
        if revenue_min is not None:
            filters["soc_camin"] = revenue_min
        
        if revenue_max is not None:
            filters["soc_camax"] = revenue_max
        
        if is_tech is not None:
            filters["uniqut_istech"] = "oui" if is_tech else "non"
        
        result = await api_client.get_societes(page=page, filters=filters)
        
        return format_response(result, max_results)
    
    except CFNewsAPIError as e:
        return json.dumps({"error": str(e)}, ensure_ascii=False)
    except Exception as e:
        return json.dumps({"error": f"Erreur inattendue: {str(e)}"}, ensure_ascii=False)


@mcp.tool()
async def search_people(
    name: Optional[str] = None,
    organization: Optional[str] = None,
    titles: Optional[List[str]] = None,
    organization_types: Optional[List[str]] = None,
    regions: Optional[List[str]] = None,
    executives_only: bool = False,
    with_email: bool = False,
    page: int = 1,
    max_results: int = 10
) -> str:
    """
    Recherche des personnalités dans le bottin CFNEWS.
    
    Args:
        name: Nom ou prénom de la personne
        organization: Organisation actuelle
        titles: Titres/fonctions (ex: ["Directeur général", "Associé(e)"])
        organization_types: Types d'organisation (ex: ["Fonds", "Avocats"])
        regions: Régions de l'organisation
        executives_only: Filtre cadres dirigeants/CODIR uniquement
        with_email: Filtre uniquement avec email renseigné
        page: Numéro de page
        max_results: Nombre maximum de résultats
    
    Returns:
        JSON formaté des personnalités trouvées
    """
    try:
        api_client = get_client()
        
        filters = {}
        
        if name:
            filters["people_nom"] = name
        
        if organization:
            filters["people_societe"] = organization
        
        if titles:
            # Quelques mappings de titres courants
            title_mapping = {
                "Directeur général": 8416,
                "Associé(e)": 8410,
                "Partner": 8408,
                "Directeur": 8406
            }
            filters["people_titres"] = [title_mapping.get(t, t) for t in titles]
        
        if organization_types:
            type_mapping = {
                "Fonds": 308,
                "Avocats": 207,
                "Banquiers": 226,
                "Conseils": 230
            }
            filters["people_type_organisation"] = [type_mapping.get(t, t) for t in organization_types]
        
        if regions:
            region_mapping = {
                "Île-de-France": 132336,
                "Auvergne-Rhône-Alpes": 132360
            }
            filters["people_region"] = [region_mapping.get(r, r) for r in regions]
        
        if executives_only:
            filters["ciblage_dirigeants"] = "Dirigeants"
        
        if with_email:
            filters["uniqut_avec_email"] = "oui"
        
        result = await api_client.get_people(page=page, filters=filters)
        
        return format_response(result, max_results)
    
    except CFNewsAPIError as e:
        return json.dumps({"error": str(e)}, ensure_ascii=False)
    except Exception as e:
        return json.dumps({"error": f"Erreur inattendue: {str(e)}"}, ensure_ascii=False)


@mcp.tool()
async def search_news(
    title: Optional[str] = None,
    themes: Optional[List[str]] = None,
    keywords: Optional[List[str]] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    page: int = 1,
    max_results: int = 10
) -> str:
    """
    Recherche des actualités CFNEWS.
    
    Args:
        title: Mots dans le titre
        themes: Thèmes (ex: ["LBO", "Levée de Fonds", "M&A"])
        keywords: Mots-clés (ex: ["capital investissement", "fintech"])
        date_from: Date de début de publication (YYYY-MM-DD)
        date_to: Date de fin de publication (YYYY-MM-DD)
        page: Numéro de page
        max_results: Nombre maximum de résultats
    
    Returns:
        JSON formaté des actualités trouvées
    """
    try:
        api_client = get_client()
        
        filters = {}
        
        if title:
            filters["title"] = title
        
        if themes:
            filters["theme"] = themes
        
        if keywords:
            filters["keyword"] = keywords
        
        if date_from:
            filters["date_start"] = date_from
        
        if date_to:
            filters["date_end"] = date_to
        
        result = await api_client.get_actualites(page=page, filters=filters)
        
        return format_response(result, max_results)
    
    except CFNewsAPIError as e:
        return json.dumps({"error": str(e)}, ensure_ascii=False)
    except Exception as e:
        return json.dumps({"error": f"Erreur inattendue: {str(e)}"}, ensure_ascii=False)


@mcp.tool()
async def get_fund_portfolio(
    fund_id: int,
    portfolio_type: str = "current"
) -> str:
    """
    Récupère le portefeuille d'un fonds d'investissement.
    
    Args:
        fund_id: ID du fonds (récupéré via search_actors)
        portfolio_type: Type de portefeuille ("current" pour actuel, "exits" pour sorties)
    
    Returns:
        JSON formaté du portefeuille
    """
    try:
        api_client = get_client()
        
        if portfolio_type == "current":
            result = await api_client.get_actor_portfolio_current(fund_id)
        elif portfolio_type == "exits":
            result = await api_client.get_actor_portfolio_exits(fund_id)
        else:
            return json.dumps({
                "error": "portfolio_type doit être 'current' ou 'exits'"
            }, ensure_ascii=False)
        
        return json.dumps(result, ensure_ascii=False, indent=2)
    
    except CFNewsAPIError as e:
        return json.dumps({"error": str(e)}, ensure_ascii=False)
    except Exception as e:
        return json.dumps({"error": f"Erreur inattendue: {str(e)}"}, ensure_ascii=False)


# Point d'entrée pour le mode serveur
if __name__ == "__main__":
    # Le serveur MCP peut être lancé en mode serveur HTTP
    # Pour Dust, on utilise le mode stdio (standard)
    mcp.run()
