"""Client pour l'API CFNEWS — v2.0"""

import httpx
from typing import Optional, Dict, Any
from urllib.parse import quote


class CFNewsAPIError(Exception):
    """Erreur lors d'une requête à l'API CFNEWS."""
    pass


class CFNewsClient:
    """Client pour interagir avec l'API CFNEWS."""

    BASE_URL = "https://api.cfnews.net/v1"

    def __init__(self, api_key: str, timeout: int = 30):
        """
        Initialise le client CFNEWS.

        Args:
            api_key: Clé API CFNEWS
            timeout: Timeout des requêtes en secondes
        """
        self.api_key = api_key
        self.timeout = timeout
        self.client = httpx.AsyncClient(
            timeout=timeout,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
        )

    async def close(self):
        """Ferme le client HTTP."""
        await self.client.aclose()

    def _build_query_string(self, params: Dict[str, Any]) -> str:
        """
        Construit la query string encodée pour l'API CFNEWS.

        Args:
            params: Dictionnaire des paramètres

        Returns:
            Query string encodée en URL
        """
        clean_params = {k: v for k, v in params.items() if v is not None}

        query_parts = []
        for key, value in clean_params.items():
            if isinstance(value, list):
                for v in value:
                    encoded_key = quote(f"{key}[]", safe="")
                    query_parts.append(f"{encoded_key}={quote(str(v), safe='')}")
            else:
                encoded_key = quote(key, safe="")
                query_parts.append(f"{encoded_key}={quote(str(value), safe='')}")

        return "&".join(query_parts)

    # ───────────────────────────────────────────────
    # Méthode de recherche générique
    # ───────────────────────────────────────────────

    async def search(
        self,
        endpoint: str,
        page: int = 1,
        query_params: Optional[Dict[str, Any]] = None,
        limit: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Effectue une recherche sur un endpoint CFNEWS.

        Args:
            endpoint: Endpoint à interroger (operation, vehicule, etc.)
            page: Numéro de page
            query_params: Paramètres de recherche
            limit: Limite de résultats

        Returns:
            Données de la réponse JSON
        """
        url = f"{self.BASE_URL}/{endpoint}"

        base_params: Dict[str, Any] = {"page": page}
        if limit:
            base_params["limit"] = limit

        query_string = ""
        if query_params:
            query_string = self._build_query_string(query_params)

        if query_string:
            base_params["q"] = query_string

        try:
            response = await self.client.get(url, params=base_params)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            raise CFNewsAPIError(
                f"Erreur HTTP {e.response.status_code}: {e.response.text}"
            )
        except httpx.RequestError as e:
            raise CFNewsAPIError(f"Erreur de requête: {str(e)}")

    # ───────────────────────────────────────────────
    # Méthode de détail générique
    # ───────────────────────────────────────────────

    async def _get_detail(self, endpoint: str, item_id: int) -> Dict[str, Any]:
        """
        Récupère le détail d'un élément par son ID.

        Args:
            endpoint: Endpoint (operation, acteur, societe, etc.)
            item_id: ID de l'élément

        Returns:
            Données JSON de la fiche détaillée
        """
        url = f"{self.BASE_URL}/{endpoint}/{item_id}"
        try:
            response = await self.client.get(url)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            raise CFNewsAPIError(
                f"Erreur HTTP {e.response.status_code}: {e.response.text}"
            )
        except httpx.RequestError as e:
            raise CFNewsAPIError(f"Erreur de requête: {str(e)}")

    # ───────────────────────────────────────────────
    # Recherches par type
    # ───────────────────────────────────────────────

    async def get_operations(
        self,
        page: int = 1,
        filters: Optional[Dict[str, Any]] = None,
        sort_by: str = "fiche_operation_operation_date_value_dt",
        sort_order: str = "descending",
    ) -> Dict[str, Any]:
        """Recherche des opérations (deals)."""
        params = filters.copy() if filters else {}
        # N'écraser le tri que s'il n'est pas déjà défini dans les filtres
        if "sort_attribute" not in params:
            params["sort_attribute"] = sort_by
        if "sort_type" not in params:
            params["sort_type"] = sort_order
        return await self.search("operation", page, params)

    async def get_vehicules(
        self,
        page: int = 1,
        filters: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Recherche des véhicules d'investissement."""
        return await self.search("vehicule", page, filters)

    async def get_acteurs(
        self,
        page: int = 1,
        filters: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Recherche des acteurs (fonds, avocats, banquiers, etc.)."""
        return await self.search("acteur", page, filters)

    async def get_societes(
        self,
        page: int = 1,
        filters: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Recherche des sociétés."""
        return await self.search("societe", page, filters)

    async def get_people(
        self,
        page: int = 1,
        filters: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Recherche des personnalités."""
        return await self.search("people", page, filters)

    async def get_mouvements(
        self,
        page: int = 1,
        filters: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Recherche des mouvements de personnalités."""
        return await self.search("mouvement", page, filters)

    async def get_actualites(
        self,
        page: int = 1,
        filters: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Recherche des actualités."""
        return await self.search("actualite", page, filters)

    # ───────────────────────────────────────────────
    # Fiches détaillées
    # ───────────────────────────────────────────────

    async def get_operation_detail(self, operation_id: int) -> Dict[str, Any]:
        """Récupère le détail complet d'une opération."""
        return await self._get_detail("operation", operation_id)

    async def get_actor_detail(self, actor_id: int) -> Dict[str, Any]:
        """Récupère la fiche complète d'un acteur."""
        return await self._get_detail("acteur", actor_id)

    async def get_company_detail(self, company_id: int) -> Dict[str, Any]:
        """Récupère la fiche complète d'une société."""
        return await self._get_detail("societe", company_id)

    async def get_people_detail(self, people_id: int) -> Dict[str, Any]:
        """Récupère la fiche complète d'une personnalité."""
        return await self._get_detail("people", people_id)

    async def get_vehicule_detail(self, vehicule_id: int) -> Dict[str, Any]:
        """Récupère la fiche complète d'un véhicule d'investissement."""
        return await self._get_detail("vehicule", vehicule_id)

    # ───────────────────────────────────────────────
    # Portefeuilles
    # ───────────────────────────────────────────────

    async def get_actor_portfolio_current(self, actor_id: int) -> Dict[str, Any]:
        """Récupère le portefeuille actuel d'un fonds."""
        url = f"{self.BASE_URL}/acteur/portfolio_now/{actor_id}"
        try:
            response = await self.client.get(url)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            raise CFNewsAPIError(
                f"Erreur HTTP {e.response.status_code}: {e.response.text}"
            )
        except httpx.RequestError as e:
            raise CFNewsAPIError(f"Erreur de requête: {str(e)}")

    async def get_actor_portfolio_exits(self, actor_id: int) -> Dict[str, Any]:
        """Récupère le portefeuille de sorties d'un fonds."""
        url = f"{self.BASE_URL}/acteur/portfolio_sortie/{actor_id}"
        try:
            response = await self.client.get(url)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            raise CFNewsAPIError(
                f"Erreur HTTP {e.response.status_code}: {e.response.text}"
            )
        except httpx.RequestError as e:
            raise CFNewsAPIError(f"Erreur de requête: {str(e)}")
