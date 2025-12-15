# Dockerfile pour le serveur MCP CFNEWS
FROM python:3.11-slim

# Définir le répertoire de travail
WORKDIR /app

# Copier les fichiers de dépendances
COPY requirements.txt .

# Installer les dépendances
RUN pip install --no-cache-dir -r requirements.txt

# Copier le code source
COPY . .

# Variables d'environnement par défaut
ENV CFNEWS_API_KEY=""
ENV PORT=8000
ENV HOST=0.0.0.0

# Exposer le port
EXPOSE 8000

# Sanity check
RUN python -c "from server import mcp; print('✅ Server imported successfully')"

# Commande de démarrage
CMD ["python", "run_server.py"]
