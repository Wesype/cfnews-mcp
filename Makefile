.PHONY: help install test run run-server docker-build docker-run setup-claude clean

help: ## Affiche cette aide
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

install: ## Installe les dépendances
	pip install -r requirements.txt

test: ## Lance les tests
	python test_server.py

run: ## Lance le serveur en mode stdio (pour Claude Desktop)
	python server.py

run-server: ## Lance le serveur en mode HTTP (pour Dust)
	python run_server.py

docker-build: ## Build l'image Docker
	docker build -t cfnews-mcp:latest .

docker-run: ## Lance le serveur avec Docker
	docker-compose up -d

docker-logs: ## Affiche les logs Docker
	docker-compose logs -f

docker-stop: ## Arrête le serveur Docker
	docker-compose down

setup-claude: ## Configure Claude Desktop
	python setup_claude_desktop.py

clean: ## Nettoie les fichiers temporaires
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name "*.log" -delete

lint: ## Vérifie le code avec flake8
	flake8 server.py utils/

format: ## Formate le code avec black
	black server.py utils/

check-env: ## Vérifie la configuration
	@if [ ! -f .env ]; then \
		echo "❌ Fichier .env manquant"; \
		echo "💡 Copiez .env.example vers .env et configurez-le"; \
		exit 1; \
	fi
	@if ! grep -q "CFNEWS_API_KEY=." .env; then \
		echo "❌ CFNEWS_API_KEY non configurée dans .env"; \
		exit 1; \
	fi
	@echo "✅ Configuration OK"

dev: check-env ## Lance en mode développement
	@echo "🚀 Démarrage en mode développement..."
	python run_server.py
