"""Plan comptable SYSCOHADA révisé — extrait de travail (classes, comptes principaux et divisionnaires usuels).

IMPORTANT : cette liste sert de base pédagogique. Les libellés doivent être confrontés au texte officiel
de l'Acte uniforme relatif au droit comptable et à l'information financière (AUDCIF, 2017) et au plan
comptable général OHADA avant d'être déclarés conformes. Chaque compte est créé avec ``verified=False``.
"""

PLAN_VERSION = 'SYSCOHADA-revise-2017'

CLASSES = {
    '1': 'Comptes de ressources durables',
    '2': 'Comptes d\'actif immobilisé',
    '3': 'Comptes de stocks',
    '4': 'Comptes de tiers',
    '5': 'Comptes de trésorerie',
    '6': 'Comptes de charges des activités ordinaires',
    '7': 'Comptes de produits des activités ordinaires',
    '8': 'Comptes des autres charges et des autres produits',
    '9': 'Comptes des engagements hors bilan et de la comptabilité analytique de gestion',
}

ACCOUNTS = [
    # Classe 1
    ('10', 'Capital'), ('101', 'Capital social'), ('102', 'Capital par dotation'), ('103', 'Capital personnel'),
    ('104', 'Compte de l\'exploitant'), ('105', 'Primes liées au capital social'), ('106', 'Écarts de réévaluation'),
    ('109', 'Apporteurs, capital souscrit non appelé'),
    ('11', 'Réserves'), ('111', 'Réserve légale'), ('112', 'Réserves statutaires ou contractuelles'),
    ('113', 'Réserves réglementées'), ('118', 'Autres réserves'),
    ('12', 'Report à nouveau'), ('121', 'Report à nouveau créditeur'), ('129', 'Report à nouveau débiteur'),
    ('13', 'Résultat net de l\'exercice'), ('130', 'Résultat en instance d\'affectation'),
    ('131', 'Résultat net : bénéfice'), ('139', 'Résultat net : perte'),
    ('14', 'Subventions d\'investissement'), ('15', 'Provisions réglementées et fonds assimilés'),
    ('16', 'Emprunts et dettes assimilées'), ('161', 'Emprunts obligataires'),
    ('162', 'Emprunts et dettes auprès des établissements de crédit'), ('165', 'Dépôts et cautionnements reçus'),
    ('166', 'Intérêts courus'),
    ('17', 'Dettes de location-acquisition'),
    ('18', 'Dettes liées à des participations et comptes de liaison'),
    ('19', 'Provisions financières pour risques et charges'), ('191', 'Provisions pour litiges'),
    ('195', 'Provisions pour impôts'), ('196', 'Provisions pour pensions et obligations similaires'),
    ('198', 'Autres provisions financières pour risques et charges'),
    # Classe 2
    ('21', 'Immobilisations incorporelles'), ('211', 'Frais de développement'),
    ('212', 'Brevets, licences, concessions et droits similaires'), ('213', 'Logiciels et sites internet'),
    ('214', 'Marques'), ('215', 'Fonds commercial'), ('216', 'Droit au bail'),
    ('22', 'Terrains'), ('222', 'Terrains nus'), ('223', 'Terrains bâtis'),
    ('23', 'Bâtiments, installations techniques et agencements'), ('231', 'Bâtiments sur sol propre'),
    ('234', 'Aménagements, agencements et installations techniques'),
    ('24', 'Matériel, mobilier et actifs biologiques'), ('241', 'Matériel et outillage industriel et commercial'),
    ('244', 'Matériel et mobilier'), ('245', 'Matériel de transport'),
    ('25', 'Avances et acomptes versés sur immobilisations'), ('26', 'Titres de participation'),
    ('27', 'Autres immobilisations financières'), ('271', 'Prêts et créances'), ('274', 'Titres immobilisés'),
    ('275', 'Dépôts et cautionnements versés'),
    ('28', 'Amortissements'), ('281', 'Amortissements des immobilisations incorporelles'),
    ('2813', 'Amortissements des logiciels et sites internet'),
    ('283', 'Amortissements des bâtiments, installations techniques et agencements'),
    ('2831', 'Amortissements des bâtiments'),
    ('284', 'Amortissements du matériel'), ('2841', 'Amortissements du matériel et outillage'),
    ('2844', 'Amortissements du matériel et mobilier'), ('2845', 'Amortissements du matériel de transport'),
    ('29', 'Dépréciations des immobilisations'),
    # Classe 3
    ('31', 'Marchandises'), ('32', 'Matières premières et fournitures liées'), ('33', 'Autres approvisionnements'),
    ('34', 'Produits en cours'), ('35', 'Services en cours'), ('36', 'Produits finis'),
    ('37', 'Produits intermédiaires et résiduels'), ('38', 'Stocks en cours de route, en consignation ou en dépôt'),
    ('39', 'Dépréciations des stocks et encours de production'),
    # Classe 4
    ('40', 'Fournisseurs et comptes rattachés'), ('401', 'Fournisseurs, dettes en compte'),
    ('402', 'Fournisseurs, effets à payer'), ('408', 'Fournisseurs, factures non parvenues'),
    ('409', 'Fournisseurs débiteurs'), ('4091', 'Fournisseurs, avances et acomptes versés'),
    ('4094', 'Fournisseurs, créances pour emballages et matériels à rendre'),
    ('4098', 'Fournisseurs, rabais, remises, ristournes et autres avoirs à obtenir'),
    ('41', 'Clients et comptes rattachés'), ('411', 'Clients'), ('412', 'Clients, effets à recevoir en portefeuille'),
    ('416', 'Créances clients litigieuses ou douteuses'), ('418', 'Clients, produits à recevoir'),
    ('419', 'Clients créditeurs'), ('4191', 'Clients, avances et acomptes reçus'),
    ('4194', 'Clients, dettes pour emballages et matériels consignés'),
    ('4198', 'Clients, rabais, remises, ristournes et autres avoirs à accorder'),
    ('42', 'Personnel'), ('421', 'Personnel, avances et acomptes'), ('422', 'Personnel, rémunérations dues'),
    ('428', 'Personnel, charges à payer et produits à recevoir'),
    ('43', 'Organismes sociaux'), ('431', 'Sécurité sociale'),
    ('44', 'État et collectivités publiques'), ('441', 'État, impôt sur les bénéfices'),
    ('442', 'État, autres impôts et taxes'), ('443', 'État, TVA facturée'), ('4431', 'TVA facturée sur ventes'),
    ('4432', 'TVA facturée sur prestations de services'), ('444', 'État, TVA due ou crédit de TVA'),
    ('4441', 'État, TVA due'), ('4449', 'État, crédit de TVA à reporter'), ('445', 'État, TVA récupérable'),
    ('4451', 'TVA récupérable sur immobilisations'), ('4452', 'TVA récupérable sur achats'),
    ('4453', 'TVA récupérable sur transport'), ('4454', 'TVA récupérable sur services extérieurs et autres charges'),
    ('447', 'État, impôts retenus à la source'), ('448', 'État, charges à payer et produits à recevoir'),
    ('46', 'Associés et groupe'),
    ('47', 'Débiteurs et créditeurs divers'), ('476', 'Charges constatées d\'avance'),
    ('477', 'Produits constatés d\'avance'),
    ('48', 'Créances et dettes hors activités ordinaires'), ('481', 'Fournisseurs d\'investissements'),
    ('485', 'Créances sur cessions d\'immobilisations'),
    ('49', 'Dépréciations et provisions pour risques à court terme (tiers)'),
    ('491', 'Dépréciations des comptes clients'), ('499', 'Provisions pour risques à court terme'),
    # Classe 5
    ('50', 'Titres de placement'), ('51', 'Valeurs à encaisser'), ('511', 'Effets à encaisser'),
    ('513', 'Chèques à encaisser'), ('52', 'Banques'), ('521', 'Banques locales'),
    ('53', 'Établissements financiers et assimilés'),
    ('56', 'Banques, crédits de trésorerie et d\'escompte'), ('561', 'Crédits de trésorerie'),
    ('565', 'Escompte de crédits ordinaires'), ('57', 'Caisse'), ('571', 'Caisse siège social'),
    ('58', 'Régies d\'avances, accréditifs et virements internes'), ('585', 'Virements de fonds'),
    ('59', 'Dépréciations et provisions pour risques à court terme (trésorerie)'),
    # Classe 6
    ('60', 'Achats et variations de stocks'), ('601', 'Achats de marchandises'), ('6015', 'Frais sur achats'),
    ('602', 'Achats de matières premières et fournitures liées'), ('603', 'Variations des stocks de biens achetés'),
    ('6031', 'Variations des stocks de marchandises'), ('6032', 'Variations des stocks de matières premières'),
    ('604', 'Achats stockés de matières et fournitures consommables'), ('605', 'Autres achats'),
    ('6051', 'Fournitures non stockables – Eau'), ('6052', 'Fournitures non stockables – Électricité'),
    ('6055', 'Fournitures de bureau'), ('608', 'Achats d\'emballages'),
    ('61', 'Transports'), ('612', 'Transports sur ventes'), ('614', 'Transports du personnel'),
    ('618', 'Autres frais de transport'),
    ('62', 'Services extérieurs'), ('621', 'Sous-traitance générale'), ('622', 'Locations et charges locatives'),
    ('624', 'Entretien, réparations, remise en état et maintenance'), ('625', 'Primes d\'assurance'),
    ('626', 'Études, recherches et documentation'), ('627', 'Publicité, publications, relations publiques'),
    ('628', 'Frais de télécommunications'),
    ('63', 'Autres services extérieurs'), ('631', 'Frais bancaires'),
    ('632', 'Rémunérations d\'intermédiaires et de conseils'), ('633', 'Frais de formation du personnel'),
    ('638', 'Autres charges externes'),
    ('64', 'Impôts et taxes'), ('641', 'Impôts et taxes directs'), ('645', 'Impôts et taxes indirects'),
    ('646', 'Droits d\'enregistrement'), ('647', 'Pénalités et amendes fiscales'),
    ('65', 'Autres charges'), ('651', 'Pertes sur créances clients et autres débiteurs'), ('658', 'Charges diverses'),
    ('659', 'Charges pour dépréciations et provisions pour risques à court terme d\'exploitation'),
    ('66', 'Charges de personnel'), ('661', 'Rémunérations directes versées au personnel national'),
    ('663', 'Indemnités forfaitaires versées au personnel'), ('664', 'Charges sociales'),
    ('67', 'Frais financiers et charges assimilées'), ('671', 'Intérêts des emprunts'), ('673', 'Escomptes accordés'),
    ('674', 'Autres intérêts'), ('675', 'Escomptes des effets de commerce'), ('676', 'Pertes de change financières'),
    ('68', 'Dotations aux amortissements'), ('681', 'Dotations aux amortissements d\'exploitation'),
    ('6812', 'Dotations aux amortissements des immobilisations incorporelles'),
    ('6813', 'Dotations aux amortissements des immobilisations corporelles'),
    ('69', 'Dotations aux provisions et aux dépréciations'),
    ('691', 'Dotations aux provisions et aux dépréciations d\'exploitation'),
    ('697', 'Dotations aux provisions et aux dépréciations financières'),
    # Classe 7
    ('70', 'Ventes'), ('701', 'Ventes de marchandises'), ('702', 'Ventes de produits finis'),
    ('703', 'Ventes de produits intermédiaires'), ('705', 'Travaux facturés'), ('706', 'Services vendus'),
    ('707', 'Produits accessoires'), ('7071', 'Ports, emballages perdus et autres frais facturés'),
    ('71', 'Subventions d\'exploitation'), ('72', 'Production immobilisée'),
    ('73', 'Variations des stocks de biens et de services produits'),
    ('75', 'Autres produits'), ('758', 'Produits divers'),
    ('759', 'Reprises de charges pour dépréciations et provisions pour risques à court terme d\'exploitation'),
    ('77', 'Revenus financiers et produits assimilés'), ('771', 'Intérêts de prêts et créances diverses'),
    ('773', 'Escomptes obtenus'), ('776', 'Gains de change financiers'),
    ('78', 'Transferts de charges'), ('781', 'Transferts de charges d\'exploitation'),
    ('79', 'Reprises de provisions, de dépréciations et autres'),
    ('791', 'Reprises de provisions et dépréciations d\'exploitation'),
    ('797', 'Reprises de provisions et dépréciations financières'),
    # Classe 8
    ('81', 'Valeurs comptables des cessions d\'immobilisations'),
    ('811', 'Valeurs comptables des cessions d\'immobilisations incorporelles'),
    ('812', 'Valeurs comptables des cessions d\'immobilisations corporelles'),
    ('82', 'Produits des cessions d\'immobilisations'), ('821', 'Produits des cessions d\'immobilisations incorporelles'),
    ('822', 'Produits des cessions d\'immobilisations corporelles'),
    ('83', 'Charges hors activités ordinaires'), ('84', 'Produits hors activités ordinaires'),
    ('85', 'Dotations hors activités ordinaires'), ('86', 'Reprises de charges, provisions et dépréciations HAO'),
    ('87', 'Participation des travailleurs'), ('88', 'Subventions d\'équilibre'),
    ('89', 'Impôts sur le résultat'), ('891', 'Impôts sur les bénéfices de l\'exercice'),
]

_LABELS = dict(ACCOUNTS)

# Comptes de la classe 8 qui sont des charges (les autres sont des produits).
CHARGE_8 = ('81', '83', '85', '87', '89')


def label_for(code: str) -> str:
    """Libellé du compte le plus précis connu pour ``code`` (ex. 4011 → Fournisseurs, dettes en compte)."""
    code = str(code).strip()
    for length in range(len(code), 1, -1):
        if code[:length] in _LABELS:
            return _LABELS[code[:length]]
    return CLASSES.get(code[:1], '')
