"""Script pour lancer le serveur MCP CFNEWS en mode HTTP."""
import os
import uvicorn
from dotenv import load_dotenv

# Charger les variables d'environnement
load_dotenv()

# Import du serveur MCP
from server import mcp

if __name__ == "__main__":
    # Configuration du serveur
    port = int(os.getenv("PORT", 8000))
    host = os.getenv("HOST", "0.0.0.0")
    
    print(f"🚀 Démarrage du serveur MCP CFNEWS sur {host}:{port}")
    print(f"📡 Le serveur sera accessible à: http://{host}:{port}")
    print(f"🔑 Clé API configurée: {'✅ Oui' if os.getenv('CFNEWS_API_KEY') else '❌ Non'}")
    
    # Lancer le serveur avec uvicorn
    uvicorn.run(
        mcp.http_app(),
        host=host,
        port=port,
        log_level="info"
    )
