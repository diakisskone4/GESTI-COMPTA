# Sécurité de BT COMPTA PRO

Ce document décrit les protections en place et les règles d'exploitation à respecter en production.
Chaque protection listée ici est couverte par un test automatisé (`backend/tests/test_security.py`).

## Authentification et sessions

| Protection | Détail |
|---|---|
| Jeton d'accès | Durée 15 min, conservé uniquement en mémoire dans le navigateur (jamais dans `localStorage`). |
| Jeton de rafraîchissement | Cookie `HttpOnly` (illisible par JavaScript), `Secure` en production, `SameSite=Strict`, limité à `/api/auth/`. |
| Rotation | Chaque rafraîchissement émet un nouveau jeton et révoque l'ancien ; un jeton volé et rejoué est refusé. |
| Déconnexion | Le jeton est révoqué côté serveur (liste noire), pas seulement effacé du navigateur. |
| Inactivité | Déconnexion automatique après 30 minutes sans activité (`VITE_IDLE_MINUTES`). |
| Changement de mot de passe | Ferme toutes les sessions sur les autres appareils. |
| Compte désactivé | Ne peut plus rafraîchir sa session ; ses jetons sont révoqués. |

## Mots de passe et force brute

- Règles Django : 8 caractères minimum, refus des mots de passe courants, entièrement numériques ou proches de l'identité.
  Indicateur de robustesse affiché à la saisie.
- Hachage **Argon2id** (recommandation OWASP, résistant aux attaques GPU) ; anciens hachages convertis à la connexion. Jamais de mot de passe en clair.
- **Limitation par IP** : 10 tentatives de connexion par minute (`THROTTLE_LOGIN`).
- **Verrouillage du compte** : 5 échecs consécutifs bloquent le compte 15 minutes, quelle que soit l'IP
  (`LOGIN_MAX_FAILURES`, `LOGIN_LOCK_MINUTES`). Un administrateur peut déverrouiller.
- Message d'erreur identique pour un compte inexistant ou un mauvais mot de passe.
- **Mot de passe oublié** : lien par e-mail valable 1 heure et à usage unique ; réponse identique que l'adresse
  existe ou non ; 5 demandes par heure maximum.

## Autorisations

- Toutes les routes exigent une connexion, sauf l'accueil, l'inscription, la connexion et la réinitialisation.
- L'inscription publique ne permet que les rôles Apprenant et Technicien comptable ; les rôles Enseignant et
  Administrateur sont attribués par un administrateur.
- Chaque utilisateur ne voit que ses propres entreprises et écritures.
- Un administrateur ne peut ni modifier son propre rôle ni désactiver son propre compte ; la plateforme conserve
  toujours au moins un administrateur actif.
- Écritures comptables validées : non modifiables, non supprimables ; correction par contre-passation tracée.

## Comptes professionnels

- Inscription « Apprenant » (`/inscription`) et inscription professionnelle (`/inscription/professionnel`) séparées.
- Technicien comptable : accès immédiat. Enseignant : compte inactif jusqu'à validation par un administrateur
  (onglet « Demandes de comptes »), car il donne accès aux corrigés et aux résultats des apprenants.
- Le demandeur et les administrateurs sont prévenus par e-mail ; un refus peut être motivé.
- Le rôle Administrateur n'est jamais accessible par inscription.

## Sujets et corrigés déposés

- Formats acceptés : PDF, Word (.docx), PNG, JPG ; 10 Mo maximum (`MAX_UPLOAD_MB`).
- Le contenu réel est contrôlé (signature binaire) : un exécutable renommé en .pdf est refusé ; les .docx contenant
  des macros sont refusés.
- Fichiers renommés aléatoirement et stockés hors du dossier public : ils ne sont accessibles qu'à travers l'API,
  après vérification des droits (sujet publié, correction publiée par l'enseignant).
- Le corrigé n'est jamais transmis aux apprenants avant sa publication ; seul l'auteur (ou un administrateur)
  peut modifier, publier ou supprimer un sujet.

## Protection des données et de l'API

- Requêtes SQL exclusivement via l'ORM Django (pas d'injection SQL possible par les paramètres).
- Paramètres d'URL numériques validés (erreur 400 au lieu d'une erreur serveur).
- Limites de taille : requêtes 2 Mo, 300 lignes par tableau de calcul, textes 200 caractères, montants plafonnés.
- Limites de fréquence : 120 calculs et 30 exports PDF/Excel par minute et par utilisateur.
- En-têtes HTTP : `Content-Security-Policy`, `X-Frame-Options: DENY`, `X-Content-Type-Options: nosniff`,
  `Referrer-Policy`, `Permissions-Policy`, `Cache-Control: no-store` sur l'API, HSTS en production.
- Protection XSS : React échappe tout contenu affiché ; aucune insertion de HTML brut.

## Traçabilité

Les actions sensibles sont enregistrées en base (onglet « Journal d'audit » de l'administration) et dans
`backend/logs/security.log` : connexions, échecs, verrouillages, déconnexions, changements et réinitialisations
de mot de passe, changements de rôle, validations et contre-passations d'écritures, création et suppression de dossiers.

## Règles d'exploitation en production

1. `SECRET_KEY` longue et aléatoire, différente pour chaque environnement ; `.env` jamais versionné.
2. `ADMIN_URL` personnalisée (ex. `gestion-interne-7f3k/`) pour ne pas exposer `/admin/`.
3. Configurer un vrai serveur SMTP (`EMAIL_HOST`…), sinon la réinitialisation de mot de passe ne fonctionne pas.
4. Ne jamais exécuter `bootstrap_data --demo` en production (comptes à mot de passe connu).
5. Sauvegardes quotidiennes copiées hors du serveur ; tester une restauration chaque trimestre.
6. Mises à jour de sécurité : `pip-audit -r backend/requirements.txt` et `npm audit --omit=dev` chaque mois.
7. Consulter `security.log` après toute alerte (pics de `auth.login_failed`, `auth.account_locked`).

## État des audits de dépendances (3 novembre 2026)

- `pip-audit` : aucune vulnérabilité connue.
- `npm audit --omit=dev` : aucune vulnérabilité dans les dépendances livrées aux utilisateurs.
