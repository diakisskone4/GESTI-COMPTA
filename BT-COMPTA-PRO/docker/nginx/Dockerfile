# Étape 1 : compilation du frontend React (PWA)
FROM node:22-alpine AS build
WORKDIR /app
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ .
RUN npm run build

# Étape 2 : Nginx sert le frontend compilé et relaie l'API vers Gunicorn
FROM nginx:1.27-alpine
COPY docker/nginx/templates/ /etc/nginx/templates/
COPY --from=build /app/dist /usr/share/nginx/html
