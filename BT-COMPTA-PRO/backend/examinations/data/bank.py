"""Banque initiale de quiz et d'examens blancs — exercices originaux rédigés pour BT COMPTA PRO.

Formats :
  ('mcq', énoncé, [(choix, correct), ...], correction, points)
  ('num', énoncé, réponse, tolérance, correction, points)
  ('entry', énoncé, [(compte, débit, crédit), ...], correction, points)
"""

Q_PATRIMOINE = ('mcq', 'La situation nette (patrimoine net) d\'une entreprise est égale à :',
                [('Biens + créances − dettes', True), ('Biens + dettes', False), ('Capital + dettes', False), ('Total de l\'actif', False)],
                'Situation nette = ce que l\'entreprise possède (biens et créances) − ce qu\'elle doit (dettes).', 1)
Q_PRUDENCE = ('mcq', 'Quel principe impose de constater les pertes probables mais pas les profits éventuels ?',
              [('Prudence', True), ('Permanence des méthodes', False), ('Coût historique', False), ('Continuité d\'exploitation', False)],
              'Le principe de prudence évite de transférer sur l\'avenir des incertitudes présentes.', 1)
Q_CAPITAUX = ('num', 'Une entreprise possède : matériel 4 000 000 ; stocks 1 500 000 ; créances clients 900 000 ; banque 600 000. '
              'Elle doit 1 200 000 à ses fournisseurs et 2 000 000 à la banque (emprunt). Calculer ses capitaux propres (FCFA).',
              '3800000', '1', 'Actif = 7 000 000 ; dettes = 3 200 000 ; capitaux propres = 7 000 000 − 3 200 000 = 3 800 000.', 2)
Q_RESULTAT = ('num', 'Total des produits de l\'exercice : 8 500 000 ; total des charges : 7 900 000. Quel est le résultat (FCFA) ?',
              '600000', '1', 'Résultat = Produits − Charges = 600 000 (bénéfice).', 1)
Q_DEBIT_ACTIF = ('mcq', 'Un compte d\'actif augmente :',
                 [('Au débit', True), ('Au crédit', False), ('Indifféremment', False)],
                 'Les comptes d\'actif et de charges augmentent au débit ; ceux de passif et de produits au crédit.', 1)
Q_CLASSE6 = ('mcq', 'Dans le SYSCOHADA révisé, la classe 6 regroupe :',
             [('Les charges des activités ordinaires', True), ('Les comptes de tiers', False), ('Les produits des activités ordinaires', False), ('Les comptes de trésorerie', False)],
             'Classe 6 : charges des activités ordinaires ; classe 7 : produits ; classe 4 : tiers ; classe 5 : trésorerie.', 1)
Q_BALANCE = ('mcq', 'Une balance générale correcte vérifie :',
             [('Total des soldes débiteurs = Total des soldes créditeurs', True), ('Total actif = Total charges', False), ('Débit = 2 × Crédit', False)],
             'Par la partie double, total débit = total crédit et donc somme des soldes débiteurs = somme des soldes créditeurs.', 1)
Q_ENTRY_ACHAT = ('entry', 'Achat de marchandises payé par chèque bancaire : 300 000 HT, TVA 18 %. Passer l\'écriture.',
                 [('601', '300000', '0'), ('4452', '54000', '0'), ('521', '0', '354000')],
                 '601 Achats de marchandises (D) 300 000 ; 4452 TVA récupérable (D) 54 000 ; 521 Banque (C) 354 000.', 3)
Q_CASCADE = ('num', 'Montant brut 800 000, remise 10 % puis rabais 5 %. Calculer le net commercial (FCFA).',
             '684000', '1', '800 000 × 0,90 = 720 000 ; 720 000 × 0,95 = 684 000.', 2)
Q_ESCOMPTE = ('num', 'Net commercial 500 000, escompte 2 %, TVA 18 %. Calculer le net à payer TTC (FCFA).',
              '578200', '1', 'Escompte 10 000 ; net financier 490 000 ; TVA 88 200 ; net à payer 578 200.', 2)
Q_773 = ('mcq', 'Chez l\'acheteur, l\'escompte obtenu est enregistré au compte :',
         [('773 Escomptes obtenus', True), ('673 Escomptes accordés', False), ('601 Achats de marchandises', False), ('4452 TVA récupérable', False)],
         'L\'escompte obtenu est un produit financier (773) ; l\'escompte accordé une charge financière (673).', 1)
Q_HT = ('num', 'Un montant TTC de 1 180 000 comprend une TVA au taux de 18 %. Quel est le montant HT (FCFA) ?',
        '1000000', '1', 'HT = 1 180 000 ÷ 1,18 = 1 000 000.', 1)
Q_ENTRY_VENTE = ('entry', 'Vente de marchandises à crédit : 600 000 HT, TVA 18 %. Passer l\'écriture chez le vendeur.',
                 [('411', '708000', '0'), ('701', '0', '600000'), ('4431', '0', '108000')],
                 '411 Clients (D) 708 000 ; 701 Ventes de marchandises (C) 600 000 ; 4431 TVA facturée (C) 108 000.', 3)
Q_CUMP = ('num', 'Stock initial : 100 unités à 1 000. Entrée : 300 unités à 1 200. Calculer le CUMP de fin de période.',
          '1150', '0.01', 'CUMP = (100 000 + 360 000) ÷ 400 = 1 150.', 2)
Q_FIFO = ('num', 'Stock initial : 100 u à 1 000 ; entrée : 200 u à 1 100 ; sortie : 150 u. Coût de la sortie en FIFO (FCFA) ?',
          '155000', '1', 'FIFO : 100 × 1 000 + 50 × 1 100 = 155 000.', 2)
Q_FIFO_DEF = ('mcq', 'La méthode FIFO (PEPS) valorise les sorties :',
              [('Au coût des lots les plus anciens', True), ('Au coût des lots les plus récents', False), ('Au coût moyen pondéré', False)],
              'Premier entré, premier sorti : on épuise d\'abord les lots les plus anciens.', 1)
Q_RAPPROCHEMENT = ('mcq', 'Des frais bancaires figurent sur le relevé mais pas dans la comptabilité. Que faire ?',
                   [('L\'entreprise les enregistre (débit 631, crédit 521)', True), ('La banque doit les annuler', False), ('On attend le relevé suivant', False)],
                   'Seules les opérations du relevé non encore comptabilisées donnent lieu à écriture chez l\'entreprise.', 1)
Q_DOTATION = ('num', 'Matériel acquis 6 000 000, mis en service le 1er avril N, durée 5 ans, amortissement linéaire, clôture le 31/12. '
              'Dotation de l\'exercice N (FCFA) ?', '900000', '1', '6 000 000 × 20 % × 9/12 = 900 000.', 2)
Q_VNC = ('num', 'Valeur d\'origine 6 000 000 ; cumul des amortissements 2 100 000. Calculer la VNC (FCFA).',
         '3900000', '1', 'VNC = 6 000 000 − 2 100 000 = 3 900 000.', 1)
Q_ENTRY_DOTATION = ('entry', 'Constater une dotation aux amortissements de 900 000 sur un matériel et outillage.',
                    [('6813', '900000', '0'), ('2841', '0', '900000')],
                    '6813 Dotations aux amortissements des immobilisations corporelles (D) ; 2841 Amortissements du matériel (C).', 2)
Q_CREANCE = ('num', 'Créance douteuse de 1 180 000 TTC (TVA 18 %), perte probable estimée à 40 %. Dépréciation à constater (FCFA) ?',
             '400000', '1', 'HT = 1 000 000 ; dépréciation = 1 000 000 × 40 % = 400 000.', 2)
Q_476 = ('mcq', 'Une charge payée d\'avance (loyer du trimestre suivant) est régularisée au compte :',
         [('476 Charges constatées d\'avance', True), ('477 Produits constatés d\'avance', False), ('408 Fournisseurs, factures non parvenues', False)],
         'La charge est retirée de l\'exercice par le crédit du compte de charge et le débit du 476.', 1)
Q_CAMV = ('num', 'Stock initial de marchandises 400 000 ; achats 2 000 000 ; stock final 550 000. Coût d\'achat des marchandises vendues (FCFA) ?',
          '1850000', '1', '2 000 000 + (400 000 − 550 000) = 1 850 000.', 2)

# BT2
Q_INCORP = ('num', 'Charges de la comptabilité générale 10 000 000 ; charges non incorporables 300 000 ; charges supplétives 500 000. '
            'Charges incorporables (FCFA) ?', '10200000', '1', '10 000 000 − 300 000 + 500 000 = 10 200 000.', 2)
Q_AUX = ('mcq', 'Un centre auxiliaire :',
         [('Fournit ses prestations à d\'autres centres et est réparti sur eux', True), ('Impute directement ses charges aux coûts des produits', False),
          ('Ne reçoit aucune charge en répartition primaire', False)],
         'Les centres auxiliaires sont vidés en répartition secondaire au profit des autres centres.', 1)
Q_UO = ('num', 'Le centre atelier totalise 1 500 000 après répartition secondaire pour 2 500 heures machine. Coût de l\'unité d\'œuvre ?',
        '600', '0.01', '1 500 000 ÷ 2 500 = 600 FCFA l\'heure machine.', 2)
Q_RA = ('num', 'Coût de production des produits vendus 4 200 000 ; coût de distribution 600 000 ; chiffre d\'affaires 5 500 000. Résultat analytique ?',
        '700000', '1', 'Coût de revient = 4 800 000 ; résultat = 5 500 000 − 4 800 000 = 700 000.', 2)
Q_TMCV = ('num', 'CA 20 000 000 ; charges variables 12 000 000. Taux de marge sur coût variable (en %) ?',
          '40', '0.01', 'MCV = 8 000 000 ; taux = 8 000 000 ÷ 20 000 000 = 40 %.', 1)
Q_SR = ('num', 'Charges fixes 6 000 000 ; taux de MCV 40 %. Seuil de rentabilité (FCFA) ?',
        '15000000', '1', 'SR = 6 000 000 ÷ 0,40 = 15 000 000.', 2)
Q_PM = ('num', 'Seuil de rentabilité 15 000 000 ; CA annuel 20 000 000 réparti uniformément. Point mort en mois ?',
        '9', '0.01', '15 000 000 ÷ 20 000 000 × 12 = 9 mois (fin septembre si l\'exercice commence en janvier).', 2)
Q_LEVIER = ('num', 'MCV 8 000 000 ; résultat 2 000 000. Levier opérationnel ?', '4', '0.01', 'Levier = MCV ÷ Résultat = 4.', 1)
Q_EQ = ('num', 'Matière : quantité réelle 5 200 kg à 95 ; quantité préétablie pour la production réelle 5 000 kg à 100. Écart sur quantité ?',
        '20000', '1', '(5 200 − 5 000) × 100 = 20 000 (défavorable).', 2)
Q_EP = ('num', 'Même énoncé : calculer l\'écart sur prix (signe compris).', '-26000', '1', '(95 − 100) × 5 200 = −26 000 (favorable).', 2)
Q_BPROD = ('num', 'Ventes prévues 1 000 unités ; stock final souhaité 200 ; stock initial 150. Quantité à produire ?',
           '1050', '0.01', '1 000 + 200 − 150 = 1 050.', 1)
Q_TRESO = ('num', 'Trésorerie de début 300 000 ; encaissements 2 000 000 ; décaissements 2 450 000. Trésorerie de fin (FCFA) ?',
           '-150000', '1', '300 000 + 2 000 000 − 2 450 000 = −150 000 : un financement est nécessaire.', 1)
Q_FRNG = ('num', 'Capitaux propres 12 000 000 ; dettes financières 5 000 000 ; actif immobilisé 14 000 000. FRNG ?',
          '3000000', '1', 'FRNG = 17 000 000 − 14 000 000 = 3 000 000.', 2)
Q_BFR = ('num', 'Stocks 2 000 000 ; créances 3 000 000 ; passif circulant 3 500 000. BFR ?',
         '1500000', '1', 'BFR = 5 000 000 − 3 500 000 = 1 500 000.', 2)
Q_TN = ('num', 'Avec FRNG = 3 000 000 et BFR = 1 500 000, quelle est la trésorerie nette ?', '1500000', '1', 'TN = FRNG − BFR = 1 500 000.', 1)
Q_LIQ = ('mcq', 'Le ratio de liquidité générale est :',
         [('Actif circulant ÷ Dettes à court terme', True), ('Capitaux propres ÷ Total passif', False), ('Résultat net ÷ CA', False)],
         'Il mesure la capacité de l\'actif circulant à couvrir les dettes à court terme.', 1)

QUIZZES = [
    {'title': 'Généralités, bilan et résultat', 'level': 'BT1', 'module': 'M2', 'kind': 'quiz', 'duration': 15,
     'questions': [Q_PATRIMOINE, Q_PRUDENCE, Q_CAPITAUX, Q_RESULTAT]},
    {'title': 'Partie double et documents comptables', 'level': 'BT1', 'module': 'M3', 'kind': 'quiz', 'duration': 15,
     'questions': [Q_DEBIT_ACTIF, Q_CLASSE6, Q_BALANCE, Q_ENTRY_ACHAT]},
    {'title': 'Factures, réductions et TVA', 'level': 'BT1', 'module': 'M5', 'kind': 'quiz', 'duration': 20,
     'questions': [Q_CASCADE, Q_ESCOMPTE, Q_773, Q_HT, Q_ENTRY_VENTE]},
    {'title': 'Gestion des stocks', 'level': 'BT1', 'module': 'M6', 'kind': 'quiz', 'duration': 15,
     'questions': [Q_FIFO_DEF, Q_CUMP, Q_FIFO]},
    {'title': 'Rapprochement bancaire et amortissements', 'level': 'BT1', 'module': 'M8', 'kind': 'quiz', 'duration': 20,
     'questions': [Q_RAPPROCHEMENT, Q_DOTATION, Q_VNC, Q_ENTRY_DOTATION]},
    {'title': 'Provisions et travaux d\'inventaire', 'level': 'BT1', 'module': 'M10', 'kind': 'quiz', 'duration': 15,
     'questions': [Q_CREANCE, Q_476, Q_CAMV]},
    {'title': 'Examen blanc BT1 n° 1', 'level': 'BT1', 'module': None, 'kind': 'mock', 'duration': 60,
     'description': 'Épreuve de synthèse couvrant l\'ensemble du programme BT1. Calculatrice autorisée.',
     'questions': [Q_CAPITAUX, Q_ENTRY_ACHAT, Q_CASCADE, Q_ESCOMPTE, Q_ENTRY_VENTE, Q_CUMP, Q_FIFO, Q_DOTATION,
                   Q_ENTRY_DOTATION, Q_CREANCE, Q_CAMV, Q_BALANCE]},
    {'title': 'Charges et calcul des coûts', 'level': 'BT2', 'module': 'M3', 'kind': 'quiz', 'duration': 20,
     'questions': [Q_INCORP, Q_AUX, Q_UO, Q_RA]},
    {'title': 'Coûts partiels et seuil de rentabilité', 'level': 'BT2', 'module': 'M5', 'kind': 'quiz', 'duration': 20,
     'questions': [Q_TMCV, Q_SR, Q_PM, Q_LEVIER]},
    {'title': 'Écarts et budgets', 'level': 'BT2', 'module': 'M6', 'kind': 'quiz', 'duration': 20,
     'questions': [Q_EQ, Q_EP, Q_BPROD, Q_TRESO]},
    {'title': 'Analyse financière', 'level': 'BT2', 'module': 'M8', 'kind': 'quiz', 'duration': 15,
     'questions': [Q_FRNG, Q_BFR, Q_TN, Q_LIQ]},
    {'title': 'Examen blanc BT2 n° 1', 'level': 'BT2', 'module': None, 'kind': 'mock', 'duration': 90,
     'description': 'Épreuve de synthèse : comptabilité analytique, gestion prévisionnelle et analyse financière.',
     'questions': [Q_INCORP, Q_UO, Q_RA, Q_TMCV, Q_SR, Q_PM, Q_EQ, Q_EP, Q_BPROD, Q_TRESO, Q_FRNG, Q_BFR]},
]
