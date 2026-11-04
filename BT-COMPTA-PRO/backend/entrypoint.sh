#!/bin/sh
# Démarrage du conteneur backend : migrations, données de référence, fichiers statiques.
set -e
python manage.py migrate --noinput
python manage.py bootstrap_data
python manage.py collectstatic --noinput
exec "$@"
