# Déploiement sur un VPS Ubuntu Server

Architecture : `nginx` (HTTPS, frontend compilé, proxy `/api`) → `backend` (Django + Gunicorn) → `db` (PostgreSQL 17),
plus `certbot` (renouvellement SSL) et `backup` (sauvegarde quotidienne de la base).

## 1. Préparer le serveur

```bash
sudo apt update && sudo apt upgrade -y
curl -fsSL https://get.docker.com | sudo sh
sudo usermod -aG docker $USER        # se reconnecter ensuite
sudo ufw allow OpenSSH && sudo ufw allow 80 && sudo ufw allow 443 && sudo ufw enable
```

Faire pointer le nom de domaine (enregistrement A) vers l'adresse IP du VPS.

## 2. Installer l'application

```bash
git clone <depot> bt-compta-pro && cd bt-compta-pro
cp .env.production.example .env
nano .env                            # DOMAIN, SECRET_KEY, DB_PASSWORD, ALLOWED_HOSTS…
chmod +x scripts/*.sh
DOMAIN=mon-domaine.ml EMAIL=admin@mon-domaine.ml ./scripts/init-ssl.sh
docker compose up -d --build
docker compose exec backend python manage.py createsuperuser
```

Au démarrage, le conteneur backend applique les migrations, charge les référentiels (`bootstrap_data`, sans comptes de
démonstration) et collecte les fichiers statiques.

## 3. Exploitation

| Action | Commande |
|---|---|
| Journaux | `docker compose logs -f backend nginx` |
| Mise à jour | `git pull && docker compose up -d --build` |
| Sauvegarde manuelle | `docker compose exec backup sh /backup.sh` |
| Restauration | `gunzip -c backups/<fichier>.sql.gz \| docker compose exec -T db psql -U $DB_USER $DB_NAME` |
| Tests | `docker compose exec backend python manage.py test tests` |

Les sauvegardes sont écrites dans `./backups` (rotation : `BACKUP_KEEP_DAYS`, 14 jours par défaut). Copiez-les
régulièrement hors du serveur (stockage externe) : une sauvegarde sur le même disque ne protège pas d'une panne du VPS.

## 4. Sécurité en production

- `DEBUG=False` est forcé par `docker-compose.yml` ; Django refuse de démarrer sans `SECRET_KEY`.
- HTTPS obligatoire (redirection 80 → 443, HSTS), cookies sécurisés, en-têtes CSP / X-Frame-Options.
- Connexion limitée à 10 tentatives par minute et par IP (`THROTTLE_LOGIN`), mots de passe validés (8 caractères min.).
- Les actions sensibles (connexions, échecs, validations, contre-passations, changements de rôle) sont tracées
  dans le journal d'audit, consultable dans l'espace administrateur.
- Ne jamais charger `bootstrap_data --demo` en production.
