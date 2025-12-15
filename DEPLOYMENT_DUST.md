# Guide de Déploiement pour Dust

Ce guide explique comment déployer le serveur MCP CFNEWS pour l'utiliser avec Dust.

## Architecture

```
┌─────────┐         ┌──────────────┐         ┌──────────────┐
│  Dust   │ ──────> │ Serveur MCP  │ ──────> │  API CFNEWS  │
│  (LLM)  │  HTTP   │   (FastMCP)  │  HTTPS  │              │
└─────────┘         └──────────────┘         └──────────────┘
```

## Options de Déploiement

### Option 1: Serveur Cloud (Recommandé)

#### Sur un VPS (ex: DigitalOcean, Scaleway, OVH)

1. **Connexion au serveur**
```bash
ssh user@votre-serveur.com
```

2. **Installation des prérequis**
```bash
# Mettre à jour le système
sudo apt update && sudo apt upgrade -y

# Installer Python 3.11
sudo apt install python3.11 python3.11-venv python3-pip -y

# Installer Git
sudo apt install git -y
```

3. **Cloner le repository**
```bash
cd /opt
sudo git clone https://github.com/votre-repo/cfnews-mcp.git
cd cfnews-mcp
```

4. **Configuration**
```bash
# Créer l'environnement virtuel
python3.11 -m venv venv
source venv/bin/activate

# Installer les dépendances
pip install -r requirements.txt

# Configurer les variables d'environnement
sudo nano .env
```

Ajoutez:
```
CFNEWS_API_KEY=votre_cle_api
PORT=8000
HOST=0.0.0.0
```

5. **Créer un service systemd**
```bash
sudo nano /etc/systemd/system/cfnews-mcp.service
```

Contenu:
```ini
[Unit]
Description=CFNEWS MCP Server
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/opt/cfnews-mcp
Environment="PATH=/opt/cfnews-mcp/venv/bin"
ExecStart=/opt/cfnews-mcp/venv/bin/python run_server.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

6. **Démarrer le service**
```bash
sudo systemctl daemon-reload
sudo systemctl enable cfnews-mcp
sudo systemctl start cfnews-mcp
sudo systemctl status cfnews-mcp
```

7. **Configuration Nginx (reverse proxy + HTTPS)**
```bash
sudo apt install nginx certbot python3-certbot-nginx -y
sudo nano /etc/nginx/sites-available/cfnews-mcp
```

Contenu:
```nginx
server {
    listen 80;
    server_name mcp.votre-domaine.com;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # WebSocket support (si nécessaire)
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

Activer:
```bash
sudo ln -s /etc/nginx/sites-available/cfnews-mcp /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx

# Obtenir un certificat SSL
sudo certbot --nginx -d mcp.votre-domaine.com
```

### Option 2: Docker sur Serveur Cloud

1. **Installation Docker**
```bash
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER
sudo apt install docker-compose -y
```

2. **Déployer avec Docker Compose**
```bash
cd /opt/cfnews-mcp

# Créer le fichier .env
cat > .env << EOF
CFNEWS_API_KEY=votre_cle_api
PORT=8000
HOST=0.0.0.0
EOF

# Lancer les containers
docker-compose up -d

# Vérifier les logs
docker-compose logs -f
```

3. **Configuration Nginx** (même que ci-dessus)

### Option 3: Platform-as-a-Service

#### Déploiement sur Render.com

1. Créer un `render.yaml`:
```yaml
services:
  - type: web
    name: cfnews-mcp
    env: python
    buildCommand: pip install -r requirements.txt
    startCommand: python run_server.py
    envVars:
      - key: CFNEWS_API_KEY
        sync: false
      - key: PORT
        value: 10000
      - key: HOST
        value: 0.0.0.0
```

2. Connecter votre repository Git à Render
3. Le déploiement se fait automatiquement

#### Déploiement sur Railway.app

1. Connecter votre repository
2. Ajouter les variables d'environnement
3. Railway détecte automatiquement Python et déploie

#### Déploiement sur Fly.io

1. Installer Fly CLI:
```bash
curl -L https://fly.io/install.sh | sh
```

2. Créer `fly.toml`:
```toml
app = "cfnews-mcp"
primary_region = "cdg"

[build]
  dockerfile = "Dockerfile"

[env]
  PORT = "8000"
  HOST = "0.0.0.0"

[[services]]
  http_checks = []
  internal_port = 8000
  protocol = "tcp"
  
  [[services.ports]]
    port = 80
    handlers = ["http"]
  
  [[services.ports]]
    port = 443
    handlers = ["tls", "http"]
```

3. Déployer:
```bash
fly launch
fly secrets set CFNEWS_API_KEY=votre_cle_api
fly deploy
```

## Configuration dans Dust

Une fois le serveur déployé:

1. Ouvrez Dust
2. Allez dans **Settings** > **Integrations** > **MCP Servers**
3. Cliquez sur **Add MCP Server**
4. Configurez:
   - **Name**: CFNEWS
   - **URL**: `https://mcp.votre-domaine.com` (ou l'URL de votre déploiement)
   - **Type**: HTTP
5. Testez la connexion
6. Activez le serveur

## Sécurité

### Protection de base

1. **Firewall**
```bash
sudo ufw allow 22/tcp
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable
```

2. **Fail2ban** (protection SSH)
```bash
sudo apt install fail2ban -y
sudo systemctl enable fail2ban
sudo systemctl start fail2ban
```

3. **Authentification** (optionnel)

Ajoutez une authentification basique dans Nginx:
```bash
sudo apt install apache2-utils -y
sudo htpasswd -c /etc/nginx/.htpasswd dust_user
```

Modifiez la config Nginx:
```nginx
location / {
    auth_basic "Protected";
    auth_basic_user_file /etc/nginx/.htpasswd;
    # ... reste de la config
}
```

### Rate Limiting

Dans Nginx, ajoutez:
```nginx
limit_req_zone $binary_remote_addr zone=mcp_limit:10m rate=10r/s;

server {
    location / {
        limit_req zone=mcp_limit burst=20 nodelay;
        # ... reste de la config
    }
}
```

## Monitoring

### Logs

```bash
# Logs système
sudo journalctl -u cfnews-mcp -f

# Logs Docker
docker-compose logs -f

# Logs Nginx
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log
```

### Healthcheck

Ajoutez un endpoint health dans `server.py`:
```python
@mcp.get("/health")
async def health():
    return {"status": "ok", "timestamp": datetime.now().isoformat()}
```

Testez:
```bash
curl https://mcp.votre-domaine.com/health
```

### Monitoring avec Uptime Robot

1. Créez un compte sur [uptimerobot.com](https://uptimerobot.com)
2. Ajoutez un monitor de type HTTP(s)
3. URL: `https://mcp.votre-domaine.com/health`
4. Configurez les alertes email/SMS

## Maintenance

### Mise à jour

```bash
cd /opt/cfnews-mcp
git pull
source venv/bin/activate
pip install -r requirements.txt --upgrade
sudo systemctl restart cfnews-mcp
```

Ou avec Docker:
```bash
cd /opt/cfnews-mcp
git pull
docker-compose down
docker-compose build
docker-compose up -d
```

### Backup

Sauvegardez régulièrement:
```bash
# Backup du code
tar -czf cfnews-mcp-backup-$(date +%Y%m%d).tar.gz /opt/cfnews-mcp

# Backup de la config
cp .env .env.backup
```

## Troubleshooting

### Le serveur ne démarre pas

```bash
# Vérifier les logs
sudo journalctl -u cfnews-mcp -n 50

# Vérifier les permissions
sudo chown -R www-data:www-data /opt/cfnews-mcp

# Tester manuellement
cd /opt/cfnews-mcp
source venv/bin/activate
python run_server.py
```

### Erreur 502 Bad Gateway

```bash
# Vérifier que le service tourne
sudo systemctl status cfnews-mcp

# Vérifier les logs Nginx
sudo tail -f /var/log/nginx/error.log

# Tester localement
curl http://localhost:8000/health
```

### Dust ne peut pas se connecter

1. Vérifiez le firewall
2. Vérifiez le certificat SSL: `sudo certbot renew --dry-run`
3. Testez l'URL depuis un autre appareil
4. Vérifiez les logs Nginx

## Coûts Estimés

- **VPS Basic** (2GB RAM): ~5-10€/mois
- **VPS Pro** (4GB RAM): ~15-20€/mois
- **Render.com**: Gratuit (avec limitations) ou ~7$/mois
- **Railway.app**: ~5$/mois
- **Fly.io**: ~5$/mois
- **Nom de domaine**: ~10€/an

## Support

Pour toute question:
1. Vérifiez les logs
2. Consultez la documentation FastMCP
3. Ouvrez une issue sur GitHub
