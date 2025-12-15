"""Script de test pour valider le serveur MCP CFNEWS."""
import asyncio
import os
from dotenv import load_dotenv
from utils.cfnews_client import CFNewsClient, CFNewsAPIError

load_dotenv()


async def test_client():
    """Teste le client API CFNEWS."""
    api_key = os.getenv("CFNEWS_API_KEY")
    
    if not api_key:
        print("❌ CFNEWS_API_KEY non définie dans .env")
        return False
    
    print("🔑 Clé API trouvée")
    client = CFNewsClient(api_key)
    
    try:
        # Test 1: Recherche d'opérations
        print("\n📊 Test 1: Recherche d'opérations...")
        result = await client.get_operations(
            page=1,
            filters={
                "sort_attribute": "fiche_operation_operation_date_value_dt",
                "sort_type": "descending"
            }
        )
        print(f"✅ {result.get('count', 0)} opérations trouvées")
        
        # Test 2: Recherche de véhicules
        print("\n🏦 Test 2: Recherche de véhicules...")
        result = await client.get_vehicules(page=1)
        print(f"✅ {result.get('count', 0)} véhicules trouvés")
        
        # Test 3: Recherche d'acteurs
        print("\n👥 Test 3: Recherche d'acteurs...")
        result = await client.get_acteurs(page=1)
        print(f"✅ {result.get('count', 0)} acteurs trouvés")
        
        # Test 4: Recherche de sociétés
        print("\n🏢 Test 4: Recherche de sociétés...")
        result = await client.get_societes(page=1)
        print(f"✅ {result.get('count', 0)} sociétés trouvées")
        
        # Test 5: Recherche de personnalités
        print("\n👤 Test 5: Recherche de personnalités...")
        result = await client.get_people(page=1)
        print(f"✅ {result.get('count', 0)} personnalités trouvées")
        
        # Test 6: Recherche d'actualités
        print("\n📰 Test 6: Recherche d'actualités...")
        result = await client.get_actualites(page=1)
        print(f"✅ {result.get('count', 0)} actualités trouvées")
        
        print("\n✨ Tous les tests sont passés avec succès!")
        return True
        
    except CFNewsAPIError as e:
        print(f"\n❌ Erreur API: {e}")
        return False
    except Exception as e:
        print(f"\n❌ Erreur inattendue: {e}")
        return False
    finally:
        await client.close()


async def test_filters():
    """Teste les filtres de recherche."""
    api_key = os.getenv("CFNEWS_API_KEY")
    
    if not api_key:
        print("❌ CFNEWS_API_KEY non définie")
        return False
    
    client = CFNewsClient(api_key)
    
    try:
        print("\n🔍 Test des filtres avancés...")
        
        # Test: Opérations LBO en 2024
        print("\n📈 Opérations LBO en 2024...")
        result = await client.get_operations(
            filters={
                "op_type": [271],  # LBO
                "depuis": "01/01/2024",
                "jusquau": "31/12/2024",
                "sort_attribute": "fiche_operation_operation_date_value_dt",
                "sort_type": "descending"
            }
        )
        print(f"✅ {result.get('total', 0)} opérations LBO trouvées en 2024")
        
        # Test: Fonds en cours de levée
        print("\n💰 Fonds en cours de levée...")
        result = await client.get_vehicules(
            filters={
                "vehicle_status": [189636]  # En cours de levée
            }
        )
        print(f"✅ {result.get('total', 0)} fonds en cours de levée")
        
        # Test: Sociétés biotech
        print("\n🧬 Sociétés biotechnologies...")
        result = await client.get_societes(
            filters={
                "sector": [124]  # Biotechnologies
            }
        )
        print(f"✅ {result.get('total', 0)} sociétés biotech trouvées")
        
        print("\n✨ Tests des filtres réussis!")
        return True
        
    except Exception as e:
        print(f"\n❌ Erreur: {e}")
        return False
    finally:
        await client.close()


async def main():
    """Lance tous les tests."""
    print("=" * 60)
    print("🧪 Tests du serveur MCP CFNEWS")
    print("=" * 60)
    
    # Test 1: Client de base
    success1 = await test_client()
    
    # Test 2: Filtres avancés
    success2 = await test_filters()
    
    print("\n" + "=" * 60)
    if success1 and success2:
        print("✅ TOUS LES TESTS SONT PASSÉS")
        print("=" * 60)
        return 0
    else:
        print("❌ CERTAINS TESTS ONT ÉCHOUÉ")
        print("=" * 60)
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)
