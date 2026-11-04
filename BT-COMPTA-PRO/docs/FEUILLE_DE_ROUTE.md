# Feuille de route

## Réalisé (phases 1 à 11, 13 et 14 — socle fonctionnel)

| Phase | Contenu livré |
|---|---|
| 1–2 | Arborescence, Django + PostgreSQL, migrations, pool de connexions |
| 3 | JWT avec rafraîchissement, 4 rôles, inscription limitée aux rôles apprenant / technicien, limitation des connexions, audit |
| 4 | Frontend React/TypeScript/Tailwind redessiné, tableau de bord par rôle, PWA installable et consultable hors ligne (catalogue) |
| 5 | Catalogue BT1 (10 modules) et BT2 (8 modules), 151 chapitres, progression par chapitre |
| 6 | Plan SYSCOHADA révisé versionné (233 comptes, statut « à vérifier »), taux et règles distincts OHADA / fiscalité |
| 7–10 | 40 calculatrices (BT1 : 18, BT2 : 22) avec étapes, écritures, PDF et Excel ; moteur comptable complet |
| 11 | 12 quiz et examens blancs, chronomètre, correction automatique, note sur 20, carnet d'erreurs |
| 13 | 55 tests automatisés (formules vérifiées à la main, partie double, verrouillage, droits d'accès) |
| 14 | Docker Compose, Gunicorn, Nginx HTTPS, Certbot, sauvegardes quotidiennes |

## Prochaines étapes

1. **Validation officielle** : confronter plan comptable, taux fiscaux et programme BT au textes officiels ; passer les
   éléments contrôlés au statut « vérifié » (champ `verified`).
2. **Contenus** : enrichir les leçons (exemples chiffrés, exercices corrigés) via l'espace enseignant ou l'administration.
3. **Phase 12 — applications natives** : empaqueter la PWA avec Capacitor (voir `mobile/README.md`).
4. **Comptabilité** : écritures d'à-nouveaux automatiques à l'ouverture d'un exercice, lettrage des comptes de tiers,
   tableau des flux de trésorerie.
5. **Abonnements** : gestion des formules et paiements (mobile money) pour les centres de formation.
