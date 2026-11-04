"""Calculatrices BT2 — analyse financière (équilibre financier et ratios).

Les seuils d'appréciation cités sont des repères pédagogiques usuels, et non des normes réglementaires.
"""
from .base import ZERO, F, Result, calculator, div, fcfa, fmt, money

BALANCE_FIELDS = [
    F('capitaux_propres', 'Capitaux propres et ressources assimilées', required=True, default='18000000'),
    F('dettes_financieres', 'Dettes financières et ressources assimilées', default='7000000', min=0),
    F('actif_immobilise', 'Actif immobilisé (net)', required=True, default='20000000', min=0),
    F('stocks', 'Stocks', default='4500000', min=0),
    F('creances', 'Créances et emplois assimilés', default='6000000', min=0),
    F('passif_circulant', 'Passif circulant (dettes fournisseurs, fiscales, sociales…)', default='5800000', min=0),
    F('tresorerie_actif', 'Trésorerie – Actif', default='1300000', min=0),
    F('tresorerie_passif', 'Trésorerie – Passif', default='1000000', min=0),
]


def _equilibre(d):
    ressources = d['capitaux_propres'] + d['dettes_financieres']
    fr = ressources - d['actif_immobilise']
    bfr = d['stocks'] + d['creances'] - d['passif_circulant']
    tn = d['tresorerie_actif'] - d['tresorerie_passif']
    return ressources, fr, bfr, tn


def _check(r, fr, bfr, tn):
    if money(fr - bfr) != money(tn):
        r.warnings.append(f'FR − BFR ({fcfa(fr - bfr)}) ≠ Trésorerie nette ({fcfa(tn)}) : le bilan saisi n\'est pas équilibré.')


@calculator('frng', 'Fonds de roulement net global (FRNG)', 'BT2', 'Analyse financière',
            'Excédent des ressources stables sur les emplois stables.', BALANCE_FIELDS)
def calc_frng(d):
    r = Result()
    ressources, fr, bfr, tn = _equilibre(d)
    r.formulas = ['Ressources stables = Capitaux propres + Dettes financières', 'FRNG = Ressources stables − Actif immobilisé']
    r.step('Ressources stables', f'{fmt(d["capitaux_propres"])} + {fmt(d["dettes_financieres"])}', ressources)
    r.step('FRNG', f'{fmt(ressources)} − {fmt(d["actif_immobilise"])}', fr)
    r.result('Ressources stables', ressources)
    r.result('Fonds de roulement net global', fr, highlight=True)
    if fr >= 0:
        r.interpretation.append('FRNG positif : les ressources stables financent la totalité des immobilisations et dégagent '
                                'une marge pour financer le cycle d\'exploitation.')
    else:
        r.interpretation.append('FRNG négatif : une partie des immobilisations est financée par des ressources à court terme, '
                                'situation risquée (règle de l\'équilibre financier minimum non respectée).')
    _check(r, fr, bfr, tn)
    return r


@calculator('bfr', 'Besoin de financement (BFR)', 'BT2', 'Analyse financière',
            'Besoin de financement né du cycle d\'exploitation.', BALANCE_FIELDS)
def calc_bfr(d):
    r = Result()
    _, fr, bfr, tn = _equilibre(d)
    r.formulas = ['BFR = Actif circulant (stocks + créances) − Passif circulant (hors trésorerie)']
    r.step('BFR', f'{fmt(d["stocks"])} + {fmt(d["creances"])} − {fmt(d["passif_circulant"])}', bfr)
    r.result('Besoin de financement', bfr, highlight=True)
    r.result('Fonds de roulement', fr)
    r.result('Couverture du BFR par le FR', 'Oui' if fr >= bfr else 'Non', unit='')
    r.interpretation.append('BFR positif : le cycle d\'exploitation doit être financé.' if bfr > 0 else
                            'BFR négatif : le cycle d\'exploitation dégage une ressource (fournisseurs payés après encaissement des clients).')
    _check(r, fr, bfr, tn)
    return r


@calculator('tresorerie-nette', 'Trésorerie nette', 'BT2', 'Analyse financière',
            'Trésorerie nette par les deux méthodes : FR − BFR et Trésorerie actif − Trésorerie passif.', BALANCE_FIELDS)
def calc_tn(d):
    r = Result()
    _, fr, bfr, tn = _equilibre(d)
    r.formulas = ['Trésorerie nette = FRNG − BFR', 'Trésorerie nette = Trésorerie actif − Trésorerie passif']
    r.step('Par le haut du bilan', f'{fmt(fr)} − {fmt(bfr)}', fr - bfr)
    r.step('Par le bas du bilan', f'{fmt(d["tresorerie_actif"])} − {fmt(d["tresorerie_passif"])}', tn)
    r.table('Équilibre financier', ['Indicateur', 'Montant'], [['FRNG', fr], ['BFR', bfr], ['Trésorerie nette', tn]])
    r.result('Trésorerie nette', tn, highlight=True)
    r.interpretation.append('Trésorerie nette positive : l\'équilibre financier est assuré.' if tn >= 0 else
                            'Trésorerie nette négative : l\'entreprise dépend de concours bancaires courants.')
    _check(r, fr, bfr, tn)
    return r


@calculator('ratios', 'Ratios financiers', 'BT2', 'Analyse financière',
            'Liquidité, solvabilité, autonomie, endettement, rentabilité et rotation.',
            [*BALANCE_FIELDS,
             F('chiffre_affaires', 'Chiffre d\'affaires HT', default='30000000', min=0),
             F('resultat_net', 'Résultat net', default='2100000'),
             F('resultat_exploitation', 'Résultat d\'exploitation', default='3200000'),
             F('creances_clients_ttc', 'Créances clients TTC', default='5000000', min=0),
             F('dettes_fournisseurs_ttc', 'Dettes fournisseurs TTC', default='3900000', min=0),
             F('achats_ttc', 'Achats TTC de l\'exercice', default='21000000', min=0),
             F('vat', 'Taux de TVA (%)', 'percent', default='18', min=0, max=100)])
def calc_ratios(d):
    r = Result()
    ac = d['stocks'] + d['creances'] + d['tresorerie_actif']
    dct = d['passif_circulant'] + d['tresorerie_passif']
    total = d['actif_immobilise'] + ac
    dettes = d['dettes_financieres'] + dct
    rows = []

    def add(name, formula, value, unit, comment):
        rows.append([name, formula, f'{fmt(value)}{unit}', comment])
        r.result(name, value, unit=unit.strip() or '')

    if dct:
        lg = div(ac, dct)
        add('Liquidité générale', 'Actif circulant ÷ Dettes à court terme', lg, '', 'Satisfaisant si > 1' if lg > 1 else 'Insuffisant (< 1)')
        lr = div(d['creances'] + d['tresorerie_actif'], dct)
        add('Liquidité réduite', '(Créances + Trésorerie) ÷ DCT', lr, '', 'Repère usuel : entre 0,7 et 1')
        li = div(d['tresorerie_actif'], dct)
        add('Liquidité immédiate', 'Trésorerie actif ÷ DCT', li, '', 'Disponibilités immédiates')
    if dettes:
        sg = div(total, dettes)
        add('Solvabilité générale', 'Total actif ÷ Total des dettes', sg, '', 'Solvable si > 1' if sg > 1 else 'Risque d\'insolvabilité')
    if total:
        af = div(d['capitaux_propres'], total) * 100
        add('Autonomie financière', 'Capitaux propres ÷ Total passif', af, ' %', 'Repère usuel : ≥ 50 %')
    if d['capitaux_propres']:
        end = div(d['dettes_financieres'], d['capitaux_propres'])
        add('Endettement', 'Dettes financières ÷ Capitaux propres', end, '', 'Capacité d\'endettement préservée si < 1' if end < 1 else 'Endettement élevé')
        rf = div(d['resultat_net'], d['capitaux_propres']) * 100
        add('Rentabilité financière', 'Résultat net ÷ Capitaux propres', rf, ' %', 'Rémunération des associés')
    if d['capitaux_propres'] + d['dettes_financieres']:
        re = div(d['resultat_exploitation'], d['capitaux_propres'] + d['dettes_financieres']) * 100
        add('Rentabilité économique', 'Résultat d\'exploitation ÷ Capitaux investis', re, ' %', 'Rentabilité de l\'outil économique')
    if d['chiffre_affaires']:
        mn = div(d['resultat_net'], d['chiffre_affaires']) * 100
        add('Marge nette', 'Résultat net ÷ CA HT', mn, ' %', 'Part du CA restant en bénéfice')
        ca_ttc = d['chiffre_affaires'] * (1 + d['vat'] / 100)
        dc = div(d['creances_clients_ttc'], ca_ttc) * 360
        add('Délai de recouvrement clients', 'Créances clients TTC ÷ CA TTC × 360', dc, ' jours', 'Durée moyenne du crédit clients')
    if d['achats_ttc']:
        dfo = div(d['dettes_fournisseurs_ttc'], d['achats_ttc']) * 360
        add('Délai de règlement fournisseurs', 'Dettes fournisseurs TTC ÷ Achats TTC × 360', dfo, ' jours', 'Durée moyenne du crédit fournisseurs')
    r.table('Tableau des ratios', ['Ratio', 'Formule', 'Valeur', 'Appréciation'], rows)
    if r.results:
        r.results[0]['highlight'] = True
    r.formulas = [f'{row[0]} = {row[1]}' for row in rows]
    r.interpretation.append('Les repères cités sont indicatifs : un ratio s\'interprète toujours dans le temps (évolution) '
                            'et par comparaison avec les entreprises du même secteur.')
    return r
