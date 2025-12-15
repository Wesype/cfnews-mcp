#!/usr/bin/env python3
"""Script pour générer la configuration Claude Desktop pour le serveur MCP CFNEWS."""

import json
import os
import sys
from pathlib import Path


def get_config_path():
    """Retourne le chemin du fichier de configuration Claude Desktop selon l'OS."""
    system = sys.platform
    
    if system == "darwin":  # macOS
        return Path.home() / "Library" / "Application Support" / "Claude" / "claude_desktop_config.json"
    elif system == "win32":  # Windows
        return Path(os.getenv("APPDATA")) / "Claude" / "claude_desktop_config.json"
    else:  # Linux et autres
        return Path.home() / ".config" / "Claude" / "claude_desktop_config.json"


def generate_config():
    """Génère la configuration pour Claude Desktop."""
    
    # Obtenir le chemin absolu du serveur
    server_path = Path(__file__).parent.absolute() / "server.py"
    
    # Vérifier si le fichier existe
    if not server_path.exists():
        print(f"❌ Erreur: server.py non trouvé à {server_path}")
        return None
    
    # Demander la clé API
    api_key = os.getenv("CFNEWS_API_KEY")
    if not api_key:
        print("⚠️  CFNEWS_API_KEY non trouvée dans l'environnement")
        api_key = input("Entrez votre clé API CFNEWS: ").strip()
    
    # Configuration
    config = {
        "mcpServers": {
            "cfnews": {
                "command": sys.executable,  # Chemin vers Python
                "args": [str(server_path)],
                "env": {
                    "CFNEWS_API_KEY": api_key
                }
            }
        }
    }
    
    return config


def merge_with_existing(new_config, config_path):
    """Fusionne la nouvelle config avec l'existante."""
    
    if config_path.exists():
        try:
            with open(config_path, 'r') as f:
                existing_config = json.load(f)
            
            # Fusionner les mcpServers
            if "mcpServers" not in existing_config:
                existing_config["mcpServers"] = {}
            
            existing_config["mcpServers"]["cfnews"] = new_config["mcpServers"]["cfnews"]
            
            return existing_config
        except json.JSONDecodeError:
            print("⚠️  Configuration existante invalide, elle sera remplacée")
            return new_config
    
    return new_config


def main():
    """Fonction principale."""
    print("=" * 60)
    print("🔧 Configuration du serveur MCP CFNEWS pour Claude Desktop")
    print("=" * 60)
    print()
    
    # Générer la configuration
    config = generate_config()
    if not config:
        return 1
    
    # Obtenir le chemin du fichier de config
    config_path = get_config_path()
    print(f"📁 Fichier de configuration: {config_path}")
    print()
    
    # Créer le répertoire si nécessaire
    config_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Fusionner avec la config existante
    final_config = merge_with_existing(config, config_path)
    
    # Afficher la configuration
    print("📝 Configuration qui sera ajoutée:")
    print(json.dumps(config, indent=2))
    print()
    
    # Demander confirmation
    response = input("Voulez-vous écrire cette configuration? (o/N): ").strip().lower()
    
    if response in ['o', 'oui', 'y', 'yes']:
        try:
            with open(config_path, 'w') as f:
                json.dump(final_config, f, indent=2)
            
            print()
            print("✅ Configuration écrite avec succès!")
            print()
            print("📋 Prochaines étapes:")
            print("1. Redémarrez Claude Desktop")
            print("2. Le serveur CFNEWS devrait apparaître dans les outils disponibles")
            print("3. Testez avec: 'Recherche des opérations LBO récentes'")
            print()
            return 0
        
        except Exception as e:
            print(f"❌ Erreur lors de l'écriture: {e}")
            return 1
    else:
        print("❌ Configuration annulée")
        print()
        print("💡 Pour configurer manuellement:")
        print(f"   1. Ouvrez: {config_path}")
        print("   2. Ajoutez la configuration ci-dessus")
        print()
        return 0


if __name__ == "__main__":
    sys.exit(main())
