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

## Expérience mobile intégrée

- Barre d'onglets adaptée au rôle, barre d'application avec bouton retour, zones protégées (encoche, barre iOS).
- Accueil en widgets (`frontend/src/modules/mobile/MobileHome.tsx`), menu complet (`/app/plus`).
- Installation guidée : invite native sur Android, instructions Safari sur iPhone et iPad (`Install.tsx`).
- Raccourcis par appui long sur l'icône (Android, Windows) et écrans de démarrage iOS (`public/splash/`).

Limite : une PWA ne peut pas ajouter de widget sur l'écran d'accueil du téléphone. Il faut pour cela une
application native (Swift/Kotlin), ce qui suppose des comptes Apple Developer et Google Play.
