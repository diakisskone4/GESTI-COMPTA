# Applications mobiles

## Aujourd'hui : application installable (PWA)

Le frontend est une PWA : une fois le site servi en HTTPS, il s'installe directement.

- **Android (Chrome)** : menu ⋮ → « Installer l'application ».
- **iPhone / iPad (Safari)** : bouton Partager → « Sur l'écran d'accueil ».

Le catalogue pédagogique et la liste des calculatrices restent consultables hors connexion ; les calculs et la
comptabilité nécessitent le serveur.

## Étape suivante : paquets Android / iOS avec Capacitor

```bash
cd frontend
npm install @capacitor/core @capacitor/cli @capacitor/android @capacitor/ios
npx cap init "BT COMPTA PRO" ml.btcomptapro.app --web-dir dist
# L'application native appelle l'API distante :
echo "VITE_API_URL=https://mon-domaine.ml/api" > .env.production
npm run build
npx cap add android && npx cap sync android && npx cap open android   # Android Studio
npx cap add ios && npx cap sync ios && npx cap open ios               # Xcode (macOS requis)
```

Le backend accepte déjà les origines `capacitor://localhost` et `http://localhost` (variable `CORS_ALLOWED_ORIGINS`).
