# BT COMPTA PRO

Plateforme malienne de formation et de gestion comptable : parcours **BT1** (comptabilité générale) et **BT2**
(comptabilité approfondie et analytique), **40 calculatrices** comptables, **moteur de comptabilité générale**
SYSCOHADA révisé et **examens blancs** corrigés automatiquement. Montants en FCFA, interface en français,
application web installable (**PWA**) sur ordinateur, Android et iPhone.

| Couche | Technologies |
|---|---|
| Backend | Python, Django 6, Django REST Framework, JWT (SimpleJWT) |
| Base de données | PostgreSQL (pool de connexions psycopg 3) |
| Frontend | React 18, TypeScript, Vite, Tailwind CSS 4, React Router, Axios, PWA (vite-plugin-pwa) |
| Documents | ReportLab (PDF), OpenPyXL (Excel) |
| Production | Docker Compose, Gunicorn, Nginx, HTTPS Let's Encrypt, sauvegardes automatiques |

## Démarrage rapide (Windows, développement)

Prérequis : Python 3.12+, Node 20+, PostgreSQL en service local.

```powershell
# 1. Backend
cd backend
copy .env.example .env            # puis renseigner DB_PASSWORD
..\.venv\Scripts\python.exe -m pip install -r requirements.txt
..\.venv\Scripts\python.exe manage.py migrate
..\.venv\Scripts\python.exe manage.py bootstrap_data --demo
..\.venv\Scripts\python.exe manage.py runserver

# 2. Frontend (autre terminal)
cd frontend
npm install
npm run dev                        # http://localhost:5173 (l'API /api est relayée vers :8000)
```

Ou en une commande : `powershell -ExecutionPolicy Bypass -File scripts\dev-start.ps1`.

Comptes de démonstration créés par `--demo` (mot de passe `BtCompta2026!`, **à supprimer en production**) :
`admin`, `enseignant`, `eleve`, `comptable` (ce dernier possède un dossier « Boutique Sahel SARL » avec des écritures validées).

## Tests

```powershell
cd backend
..\.venv\Scripts\python.exe manage.py test tests      # 55 tests (formules, moteur comptable, API, examens)
cd ..\frontend
npm run build                                          # contrôle TypeScript + build PWA
```

Les valeurs attendues des tests de formules sont recalculées à la main (commentaires dans `backend/tests/test_calculations.py`).

## Structure

```
backend/
  config/          réglages Django (sécurité, JWT, limitation des connexions, journaux)
  core/            journal d'audit, permissions par rôle, tableau de bord, commande bootstrap_data
  accounts/        utilisateurs et rôles (administrateur, enseignant, apprenant, technicien comptable)
  pedagogy/        niveaux, modules, chapitres, leçons, progression — data/catalog.py (10 modules BT1, 8 BT2)
  accounting/      entreprises, exercices, journaux, plan SYSCOHADA versionné, écritures, états — data/syscohada.py
  calculations/    moteur de calcul Decimal : engines/{bt1,stocks,ledger,analytical,budgets,financial}.py
  examinations/    quiz, examens blancs, correction automatique (QCM, calcul, saisie d'écriture), note sur 20
  reports/         génération PDF et Excel
  tests/
frontend/src/
  pages/ layouts/ components/ modules/{calculator,accounting}/ services/ hooks/ types/
docker/  scripts/  docs/  mobile/
```

## Points clés

- **Écritures** : une écriture validée reçoit un numéro séquentiel et n'est plus modifiable ni supprimable ;
  la correction se fait par **contre-passation**, journalisée dans l'audit.
- **Calculatrices** : chaque calcul renvoie formules, données, étapes, résultats, interprétation, écritures
  (équilibre vérifié automatiquement) et s'exporte en PDF / Excel.
- **Référentiels versionnés** : plan de comptes (`PlanVersion`), taux fiscaux (`TaxRate`), règles OHADA et dispositions
  fiscales maliennes (`AccountingRule`) sont distingués et portent un statut **« à vérifier »**.

## À vérifier avant usage professionnel

Ces éléments sont signalés dans l'application et ne doivent pas être présentés comme officiels sans contrôle :

- Libellés du plan comptable SYSCOHADA révisé (extrait de 233 comptes) face au texte de l'AUDCIF.
- Taux de TVA par défaut (18 %), régime et coefficients de l'amortissement dégressif, récupération de TVA sur créances
  irrécouvrables : Code général des impôts du Mali et loi de finances en vigueur.
- Correspondance du catalogue BT1/BT2 avec le programme officiel malien (intitulés, compétences, volumes horaires).
- La banque de questions est originale ; l'intégration d'annales publiques doit respecter les droits applicables.

Voir [docs/DEPLOIEMENT.md](docs/DEPLOIEMENT.md) pour la mise en production et [docs/FEUILLE_DE_ROUTE.md](docs/FEUILLE_DE_ROUTE.md) pour les phases suivantes.
