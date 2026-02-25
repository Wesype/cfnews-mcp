"""Serveur MCP pour l'API CFNEWS — v2.0"""

import os
from typing import Optional, Dict, Any, List
import json

from fastmcp import FastMCP
from dotenv import load_dotenv

from utils.cfnews_client import CFNewsClient, CFNewsAPIError

load_dotenv()

mcp = FastMCP("CFNEWS")

client: Optional[CFNewsClient] = None


# ═══════════════════════════════════════════════════════════════
# MAPPINGS DE RÉFÉRENCE
# ═══════════════════════════════════════════════════════════════

OPERATION_TYPE_MAPPING = {
    "LBO": 271,
    "M&A Corporate": 272,
    "Capital Développement": 273,
    "Capital Innovation": 274,
    "Immobilier": 275,
    "Bourse": 25006,
    "Financement": 29093,
    "Restructuration": 14447,
    "Infrastructure": 199547,
    "Build-up": 15809,
    "MBO/MBI": 15810,
    "OBO": 15811,
    "BIMBO": 15812,
    "Public to Private": 25007,
    "Retournement": 14448,
}

SECTOR_MAPPING = {
    "Aéronautique et Spatial": 291,
    "Agroalimentaire": 292,
    "Automobile": 293,
    "Biotechnologies": 124,
    "BTP et Construction": 294,
    "Chimie et Matériaux": 295,
    "Corporate Finance": 19486,
    "Distribution et Commerce": 303,
    "Énergie et Environnement": 298,
    "Hôtellerie et Tourisme": 306,
    "Immobilier": 304,
    "Industrie": 299,
    "Internet & ecommerce, eservices": 296,
    "Logiciel et services informatiques": 297,
    "Luxe et Mode": 307,
    "Médias et Telecom": 300,
    "Santé, beauté et services associés": 302,
    "Services": 301,
    "Services Financiers": 305,
    "Transport et Logistique": 308,
}

ACTOR_TYPE_MAPPING = {
    "Fonds d'investissement": 187,
    "Avocats": 188,
    "Banquiers": 189,
    "Conseils": 190,
    "Investisseurs institutionnels": 191,
    "Asset Managers": 451255,
    "Family Offices": 192,
    "Auditeurs / Due Diligence": 193,
}

REGION_MAPPING = {
    "Île-de-France": 132336,
    "Auvergne-Rhône-Alpes": 132360,
    "Bourgogne-Franche-Comté": 132347,
    "Bretagne": 132342,
    "Centre-Val de Loire": 132340,
    "Corse": 132362,
    "Grand Est": 132334,
    "Hauts-de-France": 132355,
    "Normandie": 132338,
    "Nouvelle-Aquitaine": 132349,
    "Occitanie": 132354,
    "Pays de la Loire": 132344,
    "Provence-Alpes-Côte d'Azur": 132358,
}

FUND_SEGMENT_MAPPING = {
    "LBO": 189615,
    "Capital développement": 189607,
    "Capital innovation / VC": 189608,
    "Amorçage": 189606,
    "Dette": 189609,
    "Fonds de fonds": 189610,
    "Infrastructure": 189611,
    "Immobilier": 189612,
    "Secondaire": 189613,
    "Retournement": 189614,
    "Mezzanine": 189616,
}

FUND_STATUS_MAPPING = {
    "Closé": 189639,
    "En cours de levée": 189636,
    "1er closing": 189637,
    "En préparation": 189635,
}

PEOPLE_TITLE_MAPPING = {
    "Président": 8415,
    "Directeur général": 8416,
    "Directeur": 8406,
    "Associé(e)": 8410,
    "Partner": 8408,
    "Managing Director": 8407,
    "Vice-Président": 8417,
    "Analyste": 8401,
    "Chargé d'affaires": 8404,
}

PEOPLE_ORG_TYPE_MAPPING = {
    "Fonds": 308,
    "Avocats": 207,
    "Banquiers": 226,
    "Conseils": 230,
    "Sociétés": 231,
}

COMPANY_TYPE_MAPPING = {
    "Familiale": 260,
    "Sté sous LBO": 20104,
    "Cotée": 18904,
    "Indépendante": 259,
}

SORT_ATTRIBUTE_MAPPING = {
    "date": "fiche_operation_operation_date_value_dt",
    "amount": "fiche_operation_montant_value_dt",
    "name": "fiche_operation_nom_value_s",
}


# ═══════════════════════════════════════════════════════════════
# UTILITAIRES
# ═══════════════════════════════════════════════════════════════


def get_client() -> CFNewsClient:
    """Récupère ou initialise le client API."""
    global client
    if client is None:
        api_key = os.getenv("CFNEWS_API_KEY")
        if not api_key:
            raise ValueError(
                "CFNEWS_API_KEY non définie dans les variables d'environnement"
            )
        client = CFNewsClient(api_key)
    return client


def resolve_mapping(values: List[str], mapping: Dict[str, int]) -> tuple:
    """
    Résout une liste de valeurs textuelles vers leurs IDs via un mapping.
    Match case-insensitive. Retourne (resolved_ids, warnings).
    """
    resolved = []
    warnings = []
    lower_mapping = {k.lower(): v for k, v in mapping.items()}

    for val in values:
        if val in mapping:
            resolved.append(mapping[val])
        elif val.lower() in lower_mapping:
            resolved.append(lower_mapping[val.lower()])
        elif isinstance(val, int) or (isinstance(val, str) and val.isdigit()):
            resolved.append(int(val))
        else:
            warnings.append(val)

    return resolved, warnings


def format_response(data: Dict[str, Any], max_items: int = 10) -> str:
    """Formate la réponse de l'API pour le LLM."""
    if "items" not in data:
        return json.dumps(data, ensure_ascii=False, indent=2)

    result = {
        "count": data.get("count", 0),
        "total": data.get("total", 0),
        "page": data.get("page", 1),
        "nb_pages": data.get("nb_pages", 1),
        "items": data["items"][:max_items],
    }

    total = data.get("total", 0)
    if total > max_items:
        result["note"] = (
            f"Affichage des {min(max_items, len(data['items']))} premiers résultats "
            f"sur {total} au total. Utilisez page=2, page=3... pour paginer."
        )

    return json.dumps(result, ensure_ascii=False, indent=2)


def apply_sort(filters: Dict, sort_by: Optional[str], sort_order: Optional[str]):
    """Applique les paramètres de tri aux filtres."""
    if sort_by:
        filters["sort_attribute"] = SORT_ATTRIBUTE_MAPPING.get(sort_by, sort_by)
        filters["sort_type"] = sort_order or "descending"


def _add_warnings(response: str, warnings: List[str]) -> str:
    """Ajoute des warnings à une réponse JSON si nécessaire."""
    if not warnings:
        return response
    parsed = json.loads(response)
    parsed["warnings"] = warnings
    return json.dumps(parsed, ensure_ascii=False, indent=2)


def _error(e: Exception) -> str:
    """Formate une erreur en JSON."""
    return json.dumps({"error": str(e)}, ensure_ascii=False)


# ═══════════════════════════════════════════════════════════════
# TOOLS — RECHERCHE
# ═══════════════════════════════════════════════════════════════


@mcp.tool()
async def search_operations(
    company_name: Optional[str] = None,
    investor_name: Optional[str] = None,
    investor_is_buyer: Optional[bool] = None,
    investor_is_seller: Optional[bool] = None,
    operation_types: Optional[List[str]] = None,
    sectors: Optional[List[str]] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    amount_min: Optional[float] = None,
    amount_max: Optional[float] = None,
    sort_by: Optional[str] = "date",
    sort_order: Optional[str] = "descending",
    page: int = 1,
    max_results: int = 10,
) -> str:
    """
    Recherche des opérations (deals, LBO, M&A, etc.) dans la base CFNEWS.

    📌 CAS D'USAGE :
    - Deals d'une SOCIÉTÉ CIBLE → company_name="Oxand"
    - Deals d'un INVESTISSEUR / FONDS → investor_name="Meridiam"
    - Les N derniers deals d'un fonds → investor_name + sort_by="date" + sort_order="descending"
    - Deals d'un fonds en tant qu'ACQUÉREUR uniquement → investor_is_buyer=True
    - Deals d'un fonds en tant que CÉDANT (sorties) → investor_is_seller=True

    ⚠️ Pour les deals d'un fonds, TOUJOURS utiliser investor_name plutôt que get_fund_portfolio
    quand le fonds a un grand portefeuille (>30 participations).

    Args:
        company_name: Nom de la société cible (la boîte qui se fait racheter/investir)
        investor_name: Nom de l'investisseur/acquéreur/cédant (ex: nom d'un fonds)
        investor_is_buyer: Si True, filtre l'investisseur en tant qu'acquéreur uniquement
        investor_is_seller: Si True, filtre l'investisseur en tant que cédant uniquement
        operation_types: Types d'opérations. Valeurs acceptées :
            "LBO", "M&A Corporate", "Capital Développement", "Capital Innovation",
            "Immobilier", "Bourse", "Financement", "Restructuration", "Infrastructure",
            "Build-up", "MBO/MBI", "OBO", "BIMBO", "Public to Private", "Retournement"
        sectors: Secteurs d'activité. Valeurs acceptées :
            "Aéronautique et Spatial", "Agroalimentaire", "Automobile", "Biotechnologies",
            "BTP et Construction", "Chimie et Matériaux", "Distribution et Commerce",
            "Énergie et Environnement", "Hôtellerie et Tourisme", "Immobilier", "Industrie",
            "Internet & ecommerce, eservices", "Logiciel et services informatiques",
            "Luxe et Mode", "Médias et Telecom", "Santé, beauté et services associés",
            "Services", "Services Financiers", "Transport et Logistique"
        date_from: Date de début (format DD/MM/YYYY)
        date_to: Date de fin (format DD/MM/YYYY)
        amount_min: Montant minimum en M€
        amount_max: Montant maximum en M€
        sort_by: Champ de tri — "date" (défaut), "amount", "name"
        sort_order: Ordre — "descending" (défaut) ou "ascending"
        page: Numéro de page (commence à 1)
        max_results: Nombre de résultats à afficher (défaut 10)

    Returns:
        JSON formaté des opérations trouvées avec pagination
    """
    try:
        api_client = get_client()
        filters: Dict[str, Any] = {}
        warnings: List[str] = []

        if company_name:
            filters["op_nom"] = company_name
        if investor_name:
            filters["op_invest"] = investor_name
        if investor_is_buyer:
            filters["op_buyer"] = "oui"
        if investor_is_seller:
            filters["op_solder"] = "oui"

        if operation_types:
            resolved, warns = resolve_mapping(operation_types, OPERATION_TYPE_MAPPING)
            if resolved:
                filters["op_type"] = resolved
            warnings.extend([f"Type non reconnu: '{w}'" for w in warns])

        if sectors:
            resolved, warns = resolve_mapping(sectors, SECTOR_MAPPING)
            if resolved:
                filters["sector"] = resolved
            warnings.extend([f"Secteur non reconnu: '{w}'" for w in warns])

        if date_from:
            filters["depuis"] = date_from
        if date_to:
            filters["jusquau"] = date_to
        if amount_min is not None:
            filters["Montantmin"] = amount_min
        if amount_max is not None:
            filters["Montantmax"] = amount_max

        apply_sort(filters, sort_by, sort_order)

        result = await api_client.get_operations(page=page, filters=filters)
        return _add_warnings(format_response(result, max_results), warnings)

    except (CFNewsAPIError, Exception) as e:
        return _error(e)


@mcp.tool()
async def search_funds(
    fund_name: Optional[str] = None,
    management_company: Optional[str] = None,
    fund_types: Optional[List[str]] = None,
    segments: Optional[List[str]] = None,
    status: Optional[List[str]] = None,
    amount_raised_min: Optional[float] = None,
    amount_raised_max: Optional[float] = None,
    sort_by: Optional[str] = None,
    sort_order: Optional[str] = "descending",
    page: int = 1,
    max_results: int = 10,
) -> str:
    """
    Recherche des véhicules d'investissement (fonds) dans CFNEWS.

    📌 CAS D'USAGE :
    - Trouver un fonds par nom → fund_name="Eurazeo PME III"
    - Fonds gérés par une société de gestion → management_company="Ardian"
    - Dernières levées LBO closées → segments=["LBO"], status=["Closé"]

    Args:
        fund_name: Nom du véhicule
        management_company: Société de gestion
        fund_types: Types (ex: ["FCPR", "FPCI", "SLP", "SICAV"])
        segments: Segments. Valeurs : "LBO", "Capital développement",
            "Capital innovation / VC", "Amorçage", "Dette", "Fonds de fonds",
            "Infrastructure", "Immobilier", "Secondaire", "Retournement", "Mezzanine"
        status: Statuts. Valeurs : "Closé", "En cours de levée", "1er closing", "En préparation"
        amount_raised_min: Montant levé minimum en M€
        amount_raised_max: Montant levé maximum en M€
        sort_by: Champ de tri (optionnel)
        sort_order: "descending" (défaut) ou "ascending"
        page: Numéro de page
        max_results: Nombre maximum de résultats
    """
    try:
        api_client = get_client()
        filters: Dict[str, Any] = {}
        warnings: List[str] = []

        if fund_name:
            filters["vehicle_nom"] = fund_name
        if management_company:
            filters["vehicle_soc_nom"] = management_company
        if fund_types:
            filters["vehicle_type"] = fund_types

        if segments:
            resolved, warns = resolve_mapping(segments, FUND_SEGMENT_MAPPING)
            if resolved:
                filters["vehicle_segment"] = resolved
            warnings.extend([f"Segment non reconnu: '{w}'" for w in warns])

        if status:
            resolved, warns = resolve_mapping(status, FUND_STATUS_MAPPING)
            if resolved:
                filters["vehicle_status"] = resolved
            warnings.extend([f"Statut non reconnu: '{w}'" for w in warns])

        if amount_raised_min is not None:
            filters["Montantmin"] = amount_raised_min
        if amount_raised_max is not None:
            filters["Montantmax"] = amount_raised_max

        apply_sort(filters, sort_by, sort_order)

        result = await api_client.get_vehicules(page=page, filters=filters)
        return _add_warnings(format_response(result, max_results), warnings)

    except (CFNewsAPIError, Exception) as e:
        return _error(e)


@mcp.tool()
async def search_actors(
    actor_name: Optional[str] = None,
    actor_types: Optional[List[str]] = None,
    nationalities: Optional[List[str]] = None,
    regions: Optional[List[str]] = None,
    is_tech_fund: Optional[bool] = None,
    sort_by: Optional[str] = None,
    sort_order: Optional[str] = "descending",
    page: int = 1,
    max_results: int = 10,
) -> str:
    """
    Recherche des acteurs du corporate finance (fonds, avocats, banquiers, conseils).

    📌 CAS D'USAGE :
    - Trouver un fonds par nom → actor_name="Meridiam"
    - Lister les avocats M&A → actor_types=["Avocats"]
    - Fonds tech en IdF → is_tech_fund=True, regions=["Île-de-France"]

    💡 Pour récupérer l'ID d'un fonds (nécessaire pour get_fund_portfolio), cherchez-le ici.

    Args:
        actor_name: Nom de l'acteur
        actor_types: Types. Valeurs : "Fonds d'investissement", "Avocats", "Banquiers",
            "Conseils", "Investisseurs institutionnels", "Asset Managers",
            "Family Offices", "Auditeurs / Due Diligence"
        nationalities: Codes ISO ("FR", "US", "GB", "DE", etc.)
        regions: Régions françaises. Valeurs : "Île-de-France", "Auvergne-Rhône-Alpes",
            "Bourgogne-Franche-Comté", "Bretagne", "Centre-Val de Loire", "Corse",
            "Grand Est", "Hauts-de-France", "Normandie", "Nouvelle-Aquitaine",
            "Occitanie", "Pays de la Loire", "Provence-Alpes-Côte d'Azur"
        is_tech_fund: Filtre fonds TECH uniquement
        sort_by: Champ de tri (optionnel)
        sort_order: "descending" (défaut) ou "ascending"
        page: Numéro de page
        max_results: Nombre maximum de résultats
    """
    try:
        api_client = get_client()
        filters: Dict[str, Any] = {}
        warnings: List[str] = []

        if actor_name:
            filters["acteur_nom"] = actor_name

        if actor_types:
            resolved, warns = resolve_mapping(actor_types, ACTOR_TYPE_MAPPING)
            if resolved:
                filters["acteur_domaine"] = resolved
            warnings.extend([f"Type d'acteur non reconnu: '{w}'" for w in warns])

        if nationalities:
            filters["acteur_zone"] = nationalities

        if regions:
            resolved, warns = resolve_mapping(regions, REGION_MAPPING)
            if resolved:
                filters["acteur_region"] = resolved
            warnings.extend([f"Région non reconnue: '{w}'" for w in warns])

        if is_tech_fund is not None:
            filters["uniqut_istech"] = "oui" if is_tech_fund else "non"

        apply_sort(filters, sort_by, sort_order)

        result = await api_client.get_acteurs(page=page, filters=filters)
        return _add_warnings(format_response(result, max_results), warnings)

    except (CFNewsAPIError, Exception) as e:
        return _error(e)


@mcp.tool()
async def search_companies(
    company_name: Optional[str] = None,
    company_types: Optional[List[str]] = None,
    sectors: Optional[List[str]] = None,
    regions: Optional[List[str]] = None,
    revenue_min: Optional[float] = None,
    revenue_max: Optional[float] = None,
    is_tech: Optional[bool] = None,
    sort_by: Optional[str] = None,
    sort_order: Optional[str] = "descending",
    page: int = 1,
    max_results: int = 10,
) -> str:
    """
    Recherche des sociétés dans la base CFNEWS.

    📌 CAS D'USAGE :
    - Trouver une société → company_name="Doctolib"
    - Sociétés sous LBO santé → company_types=["Sté sous LBO"], sectors=["Santé, beauté et services associés"]
    - PME tech → is_tech=True, revenue_max=50

    Args:
        company_name: Nom de la société
        company_types: Types. Valeurs : "Familiale", "Sté sous LBO", "Cotée", "Indépendante"
        sectors: Secteurs d'activité (mêmes valeurs que search_operations)
        regions: Régions françaises (mêmes valeurs que search_actors)
        revenue_min: CA minimum en M€
        revenue_max: CA maximum en M€
        is_tech: Filtre entreprises TECH uniquement
        sort_by: Champ de tri (optionnel)
        sort_order: "descending" (défaut) ou "ascending"
        page: Numéro de page
        max_results: Nombre maximum de résultats
    """
    try:
        api_client = get_client()
        filters: Dict[str, Any] = {}
        warnings: List[str] = []

        if company_name:
            filters["soc_nom"] = company_name

        if company_types:
            resolved, warns = resolve_mapping(company_types, COMPANY_TYPE_MAPPING)
            if resolved:
                filters["soc_activity"] = resolved
            warnings.extend([f"Type de société non reconnu: '{w}'" for w in warns])

        if sectors:
            resolved, warns = resolve_mapping(sectors, SECTOR_MAPPING)
            if resolved:
                filters["sector"] = resolved
            warnings.extend([f"Secteur non reconnu: '{w}'" for w in warns])

        if regions:
            resolved, warns = resolve_mapping(regions, REGION_MAPPING)
            if resolved:
                filters["soc_region"] = resolved
            warnings.extend([f"Région non reconnue: '{w}'" for w in warns])

        if revenue_min is not None:
            filters["soc_camin"] = revenue_min
        if revenue_max is not None:
            filters["soc_camax"] = revenue_max
        if is_tech is not None:
            filters["uniqut_istech"] = "oui" if is_tech else "non"

        apply_sort(filters, sort_by, sort_order)

        result = await api_client.get_societes(page=page, filters=filters)
        return _add_warnings(format_response(result, max_results), warnings)

    except (CFNewsAPIError, Exception) as e:
        return _error(e)


@mcp.tool()
async def search_people(
    name: Optional[str] = None,
    organization: Optional[str] = None,
    titles: Optional[List[str]] = None,
    organization_types: Optional[List[str]] = None,
    regions: Optional[List[str]] = None,
    executives_only: bool = False,
    with_email: bool = False,
    sort_by: Optional[str] = None,
    sort_order: Optional[str] = "descending",
    page: int = 1,
    max_results: int = 10,
) -> str:
    """
    Recherche des personnalités dans le bottin CFNEWS.

    📌 CAS D'USAGE :
    - Trouver une personne → name="Jean Dupont"
    - Partners d'un fonds → organization="Ardian", titles=["Partner"]
    - Dirigeants avec email → executives_only=True, with_email=True

    Args:
        name: Nom ou prénom de la personne
        organization: Organisation actuelle
        titles: Titres. Valeurs : "Président", "Directeur général", "Directeur",
            "Associé(e)", "Partner", "Managing Director", "Vice-Président",
            "Analyste", "Chargé d'affaires"
        organization_types: Types d'org. Valeurs : "Fonds", "Avocats", "Banquiers",
            "Conseils", "Sociétés"
        regions: Régions (mêmes valeurs que search_actors)
        executives_only: Filtre dirigeants / CODIR uniquement
        with_email: Filtre personnes avec email renseigné
        sort_by: Champ de tri (optionnel)
        sort_order: "descending" (défaut) ou "ascending"
        page: Numéro de page
        max_results: Nombre maximum de résultats
    """
    try:
        api_client = get_client()
        filters: Dict[str, Any] = {}
        warnings: List[str] = []

        if name:
            filters["people_nom"] = name
        if organization:
            filters["people_societe"] = organization

        if titles:
            resolved, warns = resolve_mapping(titles, PEOPLE_TITLE_MAPPING)
            if resolved:
                filters["people_titres"] = resolved
            warnings.extend([f"Titre non reconnu: '{w}'" for w in warns])

        if organization_types:
            resolved, warns = resolve_mapping(organization_types, PEOPLE_ORG_TYPE_MAPPING)
            if resolved:
                filters["people_type_organisation"] = resolved
            warnings.extend([f"Type d'org non reconnu: '{w}'" for w in warns])

        if regions:
            resolved, warns = resolve_mapping(regions, REGION_MAPPING)
            if resolved:
                filters["people_region"] = resolved
            warnings.extend([f"Région non reconnue: '{w}'" for w in warns])

        if executives_only:
            filters["ciblage_dirigeants"] = "Dirigeants"
        if with_email:
            filters["uniqut_avec_email"] = "oui"

        apply_sort(filters, sort_by, sort_order)

        result = await api_client.get_people(page=page, filters=filters)
        return _add_warnings(format_response(result, max_results), warnings)

    except (CFNewsAPIError, Exception) as e:
        return _error(e)


@mcp.tool()
async def search_news(
    title: Optional[str] = None,
    themes: Optional[List[str]] = None,
    keywords: Optional[List[str]] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    sort_by: Optional[str] = None,
    sort_order: Optional[str] = "descending",
    page: int = 1,
    max_results: int = 10,
) -> str:
    """
    Recherche des actualités CFNEWS.

    📌 CAS D'USAGE :
    - Dernières news LBO → themes=["LBO"]
    - Articles sur une boîte → title="Doctolib"
    - News fintech récentes → keywords=["fintech"], date_from="2024-01-01"

    Args:
        title: Mots dans le titre
        themes: Thèmes (ex: ["LBO", "Levée de Fonds", "M&A", "Nomination"])
        keywords: Mots-clés (ex: ["capital investissement", "fintech"])
        date_from: Date de début (YYYY-MM-DD)
        date_to: Date de fin (YYYY-MM-DD)
        sort_by: Champ de tri (optionnel)
        sort_order: "descending" (défaut) ou "ascending"
        page: Numéro de page
        max_results: Nombre maximum de résultats
    """
    try:
        api_client = get_client()
        filters: Dict[str, Any] = {}

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

        apply_sort(filters, sort_by, sort_order)

        result = await api_client.get_actualites(page=page, filters=filters)
        return format_response(result, max_results)

    except (CFNewsAPIError, Exception) as e:
        return _error(e)


# ═══════════════════════════════════════════════════════════════
# TOOLS — PORTEFEUILLE
# ═══════════════════════════════════════════════════════════════


@mcp.tool()
async def get_fund_portfolio(
    fund_id: int,
    portfolio_type: str = "current",
) -> str:
    """
    Récupère le portefeuille d'un fonds d'investissement.

    ⚠️ LIMITATION : Pas de pagination. Pour les gros fonds (>30 participations),
    cette méthode peut échouer → utiliser search_operations(investor_name=...) à la place.

    📌 CAS D'USAGE :
    - Portefeuille actuel d'un petit/moyen fonds → portfolio_type="current"
    - Sorties d'un fonds → portfolio_type="exits"
    - Grand fonds (Meridiam, Ardian…) → PRÉFÉRER search_operations avec investor_name

    Args:
        fund_id: ID du fonds (récupéré via search_actors)
        portfolio_type: "current" (portefeuille actuel) ou "exits" (sorties)
    """
    try:
        api_client = get_client()

        if portfolio_type not in ("current", "exits"):
            return json.dumps(
                {"error": "portfolio_type doit être 'current' ou 'exits'"},
                ensure_ascii=False,
            )

        try:
            if portfolio_type == "current":
                result = await api_client.get_actor_portfolio_current(fund_id)
            else:
                result = await api_client.get_actor_portfolio_exits(fund_id)

            return json.dumps(result, ensure_ascii=False, indent=2)

        except CFNewsAPIError as e:
            error_str = str(e).lower()
            if any(kw in error_str for kw in ("taille", "size", "limit", "too large")):
                return json.dumps(
                    {
                        "error": f"Portefeuille trop volumineux: {str(e)}",
                        "suggestion": (
                            "Utilisez search_operations(investor_name='NOM_DU_FONDS', "
                            "sort_by='date', sort_order='descending') pour obtenir "
                            "les deals de manière paginée."
                        ),
                    },
                    ensure_ascii=False,
                    indent=2,
                )
            raise

    except (CFNewsAPIError, Exception) as e:
        return _error(e)


# ═══════════════════════════════════════════════════════════════
# TOOLS — FICHES DÉTAILLÉES
# ═══════════════════════════════════════════════════════════════


@mcp.tool()
async def get_operation_detail(operation_id: int) -> str:
    """
    Récupère le détail complet d'une opération.

    📌 Après une recherche via search_operations, obtenir tous les détails d'un deal :
    valorisation, multiples, conseils impliqués, description complète, etc.

    Args:
        operation_id: ID de l'opération (récupéré via search_operations)
    """
    try:
        api_client = get_client()
        result = await api_client.get_operation_detail(operation_id)
        return json.dumps(result, ensure_ascii=False, indent=2)
    except (CFNewsAPIError, Exception) as e:
        return _error(e)


@mcp.tool()
async def get_actor_detail(actor_id: int) -> str:
    """
    Récupère la fiche complète d'un acteur.

    📌 Après search_actors, obtenir la fiche détaillée :
    équipe, AUM, historique, bureaux, spécialités, etc.

    Args:
        actor_id: ID de l'acteur (récupéré via search_actors)
    """
    try:
        api_client = get_client()
        result = await api_client.get_actor_detail(actor_id)
        return json.dumps(result, ensure_ascii=False, indent=2)
    except (CFNewsAPIError, Exception) as e:
        return _error(e)


@mcp.tool()
async def get_company_detail(company_id: int) -> str:
    """
    Récupère la fiche complète d'une société.

    📌 Après search_companies, obtenir la fiche détaillée :
    CA, effectifs, actionnariat, historique des opérations, etc.

    Args:
        company_id: ID de la société (récupéré via search_companies)
    """
    try:
        api_client = get_client()
        result = await api_client.get_company_detail(company_id)
        return json.dumps(result, ensure_ascii=False, indent=2)
    except (CFNewsAPIError, Exception) as e:
        return _error(e)


@mcp.tool()
async def get_people_detail(people_id: int) -> str:
    """
    Récupère la fiche complète d'une personnalité.

    📌 Après search_people, obtenir le profil détaillé :
    parcours, coordonnées, historique de postes, etc.

    Args:
        people_id: ID de la personne (récupéré via search_people)
    """
    try:
        api_client = get_client()
        result = await api_client.get_people_detail(people_id)
        return json.dumps(result, ensure_ascii=False, indent=2)
    except (CFNewsAPIError, Exception) as e:
        return _error(e)


@mcp.tool()
async def get_fund_detail(vehicule_id: int) -> str:
    """
    Récupère la fiche complète d'un véhicule d'investissement.

    📌 Après search_funds, obtenir les détails :
    taille cible, montant levé, investisseurs, vintage, etc.

    Args:
        vehicule_id: ID du véhicule (récupéré via search_funds)
    """
    try:
        api_client = get_client()
        result = await api_client.get_vehicule_detail(vehicule_id)
        return json.dumps(result, ensure_ascii=False, indent=2)
    except (CFNewsAPIError, Exception) as e:
        return _error(e)


# ═══════════════════════════════════════════════════════════════
# TOOLS — RÉFÉRENTIEL
# ═══════════════════════════════════════════════════════════════


@mcp.tool()
async def get_reference_data(category: str) -> str:
    """
    Retourne les valeurs de référence acceptées pour les filtres de recherche.

    Args:
        category: Catégorie. Valeurs acceptées :
            "operation_types", "sectors", "actor_types", "regions",
            "fund_segments", "fund_status", "people_titles",
            "people_org_types", "company_types"
    """
    REFERENCE_MAP = {
        "operation_types": OPERATION_TYPE_MAPPING,
        "sectors": SECTOR_MAPPING,
        "actor_types": ACTOR_TYPE_MAPPING,
        "regions": REGION_MAPPING,
        "fund_segments": FUND_SEGMENT_MAPPING,
        "fund_status": FUND_STATUS_MAPPING,
        "people_titles": PEOPLE_TITLE_MAPPING,
        "people_org_types": PEOPLE_ORG_TYPE_MAPPING,
        "company_types": COMPANY_TYPE_MAPPING,
    }

    if category not in REFERENCE_MAP:
        return json.dumps(
            {
                "error": f"Catégorie '{category}' non reconnue",
                "available_categories": list(REFERENCE_MAP.keys()),
            },
            ensure_ascii=False,
            indent=2,
        )

    return json.dumps(
        {
            "category": category,
            "values": REFERENCE_MAP[category],
            "note": "Utilisez les noms (clés) dans vos appels, le mapping vers les IDs est automatique.",
        },
        ensure_ascii=False,
        indent=2,
    )


# ═══════════════════════════════════════════════════════════════
# POINT D'ENTRÉE
# ═══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    mcp.run()
