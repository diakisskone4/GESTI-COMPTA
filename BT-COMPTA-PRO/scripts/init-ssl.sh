#!/bin/sh
# Obtention initiale du certificat Let's Encrypt (à lancer une seule fois sur le VPS).
# Usage : DOMAIN=mon-domaine.ml EMAIL=moi@exemple.ml ./scripts/init-ssl.sh
set -e
: "${DOMAIN:?Définir DOMAIN}"
: "${EMAIL:?Définir EMAIL}"
mkdir -p certbot/conf certbot/www

# Certificat temporaire auto-signé pour permettre à Nginx de démarrer
mkdir -p "certbot/conf/live/$DOMAIN"
openssl req -x509 -nodes -newkey rsa:2048 -days 1 -subj "/CN=$DOMAIN" \
  -keyout "certbot/conf/live/$DOMAIN/privkey.pem" -out "certbot/conf/live/$DOMAIN/fullchain.pem"
docker compose up -d nginx

# Remplacement par le vrai certificat
rm -rf "certbot/conf/live/$DOMAIN"
docker compose run --rm --entrypoint certbot certbot certonly --webroot -w /var/www/certbot \
  -d "$DOMAIN" --email "$EMAIL" --agree-tos --no-eff-email
docker compose restart nginx
echo "Certificat installé pour $DOMAIN."
