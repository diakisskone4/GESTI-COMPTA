"""Calculatrices BT2 — comptabilité analytique de gestion."""
from decimal import Decimal

from .base import (ZERO, CalculationError, F, Result, calculator, div, fcfa, fmt, fpct, money, options, pct)

# --------------------------------------------------------------------------------------
# Charges incorporables
# --------------------------------------------------------------------------------------


@calculator('charges-incorporables', 'Charges incorporables, directes et indirectes', 'BT2', 'Comptabilité analytique',
            'Passage des charges de la comptabilité générale aux charges de la comptabilité analytique.',
            [
                F('charges_cg', 'Charges de la comptabilité générale (classe 6)', required=True, min=0),
                F('non_incorporables', 'Charges non incorporables', default='0', min=0),
                F('capital', 'Capitaux propres (pour la rémunération des capitaux)', default='0', min=0),
                F('taux_remuneration', 'Taux de rémunération des capitaux propres (%)', 'percent', default='0', min=0, max=100),
                F('remuneration_exploitant', 'Rémunération de l\'exploitant (supplétive)', default='0', min=0),
                F('directes', 'Dont charges directes', default='0', min=0),
            ])
def calc_incorporables(d):
    r = Result()
    remu_cap = money(d['capital'] * pct(d['taux_remuneration']))
    suppletives = remu_cap + d['remuneration_exploitant']
    incorp = d['charges_cg'] - d['non_incorporables'] + suppletives
    indirectes = incorp - d['directes']
    if indirectes < 0:
        raise CalculationError('Les charges directes dépassent les charges incorporables.', 'directes')
    r.formulas = ['Charges supplétives = Rémunération des capitaux propres + Rémunération de l\'exploitant',
                  'Charges incorporables = Charges CG − Charges non incorporables + Charges supplétives',
                  'Charges indirectes = Charges incorporables − Charges directes']
    r.step('Rémunération des capitaux propres', f'{fmt(d["capital"])} × {fmt(d["taux_remuneration"])} %', remu_cap)
    r.step('Charges supplétives', f'{fmt(remu_cap)} + {fmt(d["remuneration_exploitant"])}', suppletives)
    r.step('Charges incorporables', f'{fmt(d["charges_cg"])} − {fmt(d["non_incorporables"])} + {fmt(suppletives)}', incorp)
    r.step('Charges indirectes', f'{fmt(incorp)} − {fmt(d["directes"])}', indirectes)
    r.result('Charges supplétives', suppletives)
    r.result('Charges incorporables', incorp, highlight=True)
    r.result('Charges directes', d['directes'])
    r.result('Charges indirectes (à répartir)', indirectes)
    r.interpretation.append('Les charges directes s\'affectent sans calcul intermédiaire à un coût ; les charges indirectes '
                            'transitent par les centres d\'analyse avant d\'être imputées via les unités d\'œuvre.')
    return r


# --------------------------------------------------------------------------------------
# Tableau de répartition (primaire, secondaire, unités d'œuvre)
# --------------------------------------------------------------------------------------

KIND = options(('aux', 'Auxiliaire'), ('main', 'Principale'))


def _solve(matrix: list[list[Decimal]], vector: list[Decimal]) -> list[Decimal]:
    """Résout A·x = b par élimination de Gauss (taille réduite : sections auxiliaires)."""
    n = len(vector)
    a = [row[:] + [vector[i]] for i, row in enumerate(matrix)]
    for col in range(n):
        pivot = max(range(col, n), key=lambda i: abs(a[i][col]))
        if a[pivot][col] == 0:
            raise CalculationError('Les prestations réciproques entre centres auxiliaires forment un système sans solution '
                                   '(un centre se redistribue intégralement à lui-même ?).', 'transfers')
        a[col], a[pivot] = a[pivot], a[col]
        for i in range(n):
            if i != col:
                factor = a[i][col] / a[col][col]
                a[i] = [x - factor * y for x, y in zip(a[i], a[col])]
    return [a[i][n] / a[i][i] for i in range(n)]


@calculator('repartition', 'Tableau de répartition des charges indirectes', 'BT2', 'Comptabilité analytique',
            'Répartition primaire, répartition secondaire (avec prestations réciproques) et coût des unités d\'œuvre.',
            [
                F('sections', 'Centres d\'analyse', 'table', required=True, columns=[
                    F('name', 'Centre', 'text'),
                    F('kind', 'Type', 'select', options=KIND),
                    F('primary', 'Total répartition primaire', 'money'),
                    F('uo', 'Nature de l\'unité d\'œuvre', 'text'),
                    F('uo_count', 'Nombre d\'unités d\'œuvre', 'number', min=0),
                ], default=[
                    {'name': 'Administration', 'kind': 'aux', 'primary': '600000', 'uo': '', 'uo_count': ''},
                    {'name': 'Entretien', 'kind': 'aux', 'primary': '400000', 'uo': '', 'uo_count': ''},
                    {'name': 'Approvisionnement', 'kind': 'main', 'primary': '500000', 'uo': 'kg de matière achetée', 'uo_count': '10000'},
                    {'name': 'Atelier', 'kind': 'main', 'primary': '1500000', 'uo': 'heure machine', 'uo_count': '2000'},
                    {'name': 'Distribution', 'kind': 'main', 'primary': '300000', 'uo': '100 F de CA', 'uo_count': '45000'},
                ]),
                F('transfers', 'Clés de répartition secondaire', 'table', columns=[
                    F('source', 'Du centre (auxiliaire)', 'text'),
                    F('target', 'Vers le centre', 'text'),
                    F('percent', 'Pourcentage', 'percent', min=0, max=100),
                ], default=[
                    {'source': 'Administration', 'target': 'Entretien', 'percent': '10'},
                    {'source': 'Administration', 'target': 'Approvisionnement', 'percent': '20'},
                    {'source': 'Administration', 'target': 'Atelier', 'percent': '50'},
                    {'source': 'Administration', 'target': 'Distribution', 'percent': '20'},
                    {'source': 'Entretien', 'target': 'Administration', 'percent': '10'},
                    {'source': 'Entretien', 'target': 'Approvisionnement', 'percent': '20'},
                    {'source': 'Entretien', 'target': 'Atelier', 'percent': '60'},
                    {'source': 'Entretien', 'target': 'Distribution', 'percent': '10'},
                ]),
            ])
def calc_repartition(d):
    r = Result()
    sections = d['sections']
    names = [s['name'] for s in sections]
    if len(set(names)) != len(names) or '' in names:
        raise CalculationError('Chaque centre doit avoir un nom unique.', 'sections')
    aux = [s['name'] for s in sections if s['kind'] == 'aux']
    index = {n: i for i, n in enumerate(aux)}
    shares: dict[tuple[str, str], Decimal] = {}
    for t in d['transfers']:
        if t['source'] not in index:
            raise CalculationError(f'« {t["source"]} » n\'est pas un centre auxiliaire déclaré.', 'transfers')
        if t['target'] not in names:
            raise CalculationError(f'Centre de destination inconnu : « {t["target"]} ».', 'transfers')
        if t['target'] == t['source']:
            raise CalculationError('Un centre ne peut pas se répartir sur lui-même.', 'transfers')
        shares[(t['source'], t['target'])] = shares.get((t['source'], t['target']), ZERO) + pct(t['percent'])
    for a in aux:
        total = sum((v for (s, _), v in shares.items() if s == a), ZERO)
        if total != 1:
            r.warnings.append(f'Le centre auxiliaire « {a} » est réparti à {fpct(total)} (il devrait l\'être à 100 %).')
    primary = {s['name']: s['primary'] for s in sections}
    # T_a = P_a + Σ_b share(b→a) T_b   →   T_a − Σ share(b→a) T_b = P_a
    matrix = [[(Decimal(1) if i == j else ZERO) - shares.get((b, a), ZERO) for j, b in enumerate(aux)] for i, a in enumerate(aux)]
    totals_aux = dict(zip(aux, _solve(matrix, [primary[a] for a in aux]))) if aux else {}
    r.formulas = ['Répartition primaire : affectation des charges indirectes aux centres selon les clés',
                  'Prestations réciproques : Total centre auxiliaire = Primaire + part reçue des autres auxiliaires',
                  'Répartition secondaire : chaque auxiliaire est réparti sur les autres centres selon les pourcentages',
                  'Coût de l\'unité d\'œuvre = Total du centre principal après répartition secondaire ÷ Nombre d\'unités d\'œuvre']
    for a in aux:
        received = [f'{fmt(shares[(b, a)] * 100)} % × {b}' for b in aux if (b, a) in shares]
        r.step(f'Total à répartir — {a}', f'{fmt(primary[a])}' + (' + ' + ' + '.join(received) if received else ''), money(totals_aux[a]))
    rows = [['Répartition primaire', *[primary[n] for n in names]]]
    for a in aux:
        row = [f'Répartition de « {a} »']
        for n in names:
            if n == a:
                row.append(-money(totals_aux[a]))
            else:
                row.append(money(totals_aux[a] * shares.get((a, n), ZERO)) or '')
        rows.append(row)
    finals = {}
    for n in names:
        if n in totals_aux:
            finals[n] = primary[n] - totals_aux[n] + sum((totals_aux[a] * shares.get((a, n), ZERO) for a in aux), ZERO)
        else:
            finals[n] = primary[n] + sum((totals_aux[a] * shares.get((a, n), ZERO) for a in aux), ZERO)
    rows.append(['Total répartition secondaire', *[money(finals[n]) for n in names]])
    rows.append(['Nature de l\'UO', *[s['uo'] if s['kind'] == 'main' else '' for s in sections]])
    rows.append(['Nombre d\'UO', *[s['uo_count'] if s['kind'] == 'main' and s['uo_count'] else '' for s in sections]])
    costs = []
    for s in sections:
        if s['kind'] == 'main' and s['uo_count']:
            cost = div(finals[s['name']], s['uo_count'])
            costs.append(money(cost))
            r.result(f'Coût de l\'UO — {s["name"]}', money(cost), highlight=True)
        else:
            costs.append('')
    rows.append(['Coût de l\'UO', *costs])
    r.table('Tableau de répartition des charges indirectes', ['', *names], rows)
    total_primary = sum(primary.values(), ZERO)
    total_main = sum((finals[n] for n in names if n not in totals_aux), ZERO)
    r.result('Total des charges indirectes', total_primary)
    if money(total_primary) != money(total_main):
        r.warnings.append('Le total des centres principaux ne reprend pas l\'intégralité des charges indirectes : vérifier les clés.')
    r.interpretation.append('Après répartition secondaire, les centres auxiliaires sont soldés (à zéro) : toutes les charges '
                            'indirectes se retrouvent dans les centres principaux, qui les imputent aux coûts.')
    return r


@calculator('cout-unite-oeuvre', 'Coût de l\'unité d\'œuvre / taux de frais', 'BT2', 'Comptabilité analytique',
            'Coût d\'une unité d\'œuvre (ou taux de frais pour une assiette en valeur) et imputation à un coût.',
            [
                F('total', 'Total du centre après répartition secondaire', required=True, min=0),
                F('count', 'Nombre d\'unités d\'œuvre (ou assiette de frais)', 'number', required=True, min=0),
                F('consumed', 'Unités consommées par le produit étudié', 'number', default='0', min=0),
            ])
def calc_cout_uo(d):
    r = Result()
    cost = div(d['total'], d['count'], 'nombre d\'unités d\'œuvre')
    imputed = money(cost * d['consumed'])
    r.formulas = ['Coût de l\'UO = Total du centre ÷ Nombre d\'UO', 'Charges imputées = Coût de l\'UO × UO consommées']
    r.step('Coût de l\'unité d\'œuvre', f'{fmt(d["total"])} ÷ {fmt(d["count"])}', money(cost))
    r.result('Coût de l\'unité d\'œuvre', money(cost), highlight=True)
    if d['consumed']:
        r.step('Charges imputées', f'{fmt(money(cost))} × {fmt(d["consumed"])}', imputed)
        r.result('Charges indirectes imputées', imputed)
    return r


# --------------------------------------------------------------------------------------
# Coûts : achat, production, distribution, revient, résultat analytique
# --------------------------------------------------------------------------------------

COST_COLUMNS = [
    F('element', 'Élément', 'text'),
    F('nature', 'Nature', 'select', options=options(('direct', 'Charge directe'), ('indirect', 'Charge indirecte'))),
    F('quantity', 'Quantité', 'number', min=0),
    F('unit_cost', 'Coût unitaire', 'money', min=0),
]


def _cost_table(r: Result, title: str, lines: list[dict]) -> tuple[Decimal, Decimal, Decimal]:
    rows = []
    direct = indirect = ZERO
    for l in lines:
        amount = money(l['quantity'] * l['unit_cost'])
        rows.append([l['element'] or '—', 'Directe' if l['nature'] == 'direct' else 'Indirecte', l['quantity'], l['unit_cost'], amount])
        if l['nature'] == 'indirect':
            indirect += amount
        else:
            direct += amount
    total = direct + indirect
    r.table(title, ['Élément', 'Nature', 'Quantité', 'Coût unitaire', 'Montant'], rows, footer=['Total', '', '', '', total])
    return direct, indirect, total


@calculator('cout-achat', 'Coût d\'achat des matières / marchandises', 'BT2', 'Calcul des coûts',
            'Prix d\'achat + frais directs + charges indirectes du centre approvisionnement.',
            [
                F('lines', 'Éléments du coût d\'achat', 'table', required=True, columns=COST_COLUMNS, default=[
                    {'element': 'Prix d\'achat matière M', 'nature': 'direct', 'quantity': '10000', 'unit_cost': '450'},
                    {'element': 'Frais de transport', 'nature': 'direct', 'quantity': '10000', 'unit_cost': '15'},
                    {'element': 'Centre approvisionnement (kg)', 'nature': 'indirect', 'quantity': '10000', 'unit_cost': '62'},
                ]),
                F('quantity', 'Quantité achetée', 'number', required=True, min=0, default='10000'),
            ])
def calc_cout_achat(d):
    r = Result()
    r.formulas = ['Coût d\'achat = Prix d\'achat + Frais d\'achat directs + Charges indirectes d\'approvisionnement',
                  'Coût d\'achat unitaire = Coût d\'achat total ÷ Quantité achetée']
    direct, indirect, total = _cost_table(r, 'Coût d\'achat', d['lines'])
    unit = div(total, d['quantity'], 'quantité achetée')
    r.step('Coût d\'achat unitaire', f'{fmt(total)} ÷ {fmt(d["quantity"])}', money(unit))
    r.result('Charges directes', direct)
    r.result('Charges indirectes', indirect)
    r.result('Coût d\'achat total', total, highlight=True)
    r.result('Coût d\'achat unitaire', money(unit))
    r.interpretation.append('Ce coût unitaire sert à valoriser les entrées en stock de matières (puis les sorties au CUMP ou en FIFO).')
    return r


@calculator('cout-production', 'Coût de production', 'BT2', 'Calcul des coûts',
            'Matières consommées + main-d\'œuvre directe + charges des centres de production ± en-cours.',
            [
                F('lines', 'Éléments du coût de production', 'table', required=True, columns=COST_COLUMNS, default=[
                    {'element': 'Matière M consommée (kg)', 'nature': 'direct', 'quantity': '8000', 'unit_cost': '527'},
                    {'element': 'Main-d\'œuvre directe (h)', 'nature': 'direct', 'quantity': '1500', 'unit_cost': '2500'},
                    {'element': 'Centre atelier (heure machine)', 'nature': 'indirect', 'quantity': '2000', 'unit_cost': '1100'},
                ]),
                F('wip_start', 'En-cours initial', default='0', min=0),
                F('wip_end', 'En-cours final', default='0', min=0),
                F('quantity', 'Quantité produite', 'number', required=True, min=0, default='4000'),
            ])
def calc_cout_production(d):
    r = Result()
    r.formulas = ['Coût de production = Matières consommées + MOD + Charges indirectes de production + En-cours initial − En-cours final',
                  'Coût unitaire = Coût de production ÷ Quantité produite']
    direct, indirect, total = _cost_table(r, 'Coût de production', d['lines'])
    cp = total + d['wip_start'] - d['wip_end']
    unit = div(cp, d['quantity'], 'quantité produite')
    r.step('Coût de production', f'{fmt(total)} + {fmt(d["wip_start"])} − {fmt(d["wip_end"])}', cp)
    r.step('Coût unitaire', f'{fmt(cp)} ÷ {fmt(d["quantity"])}', money(unit))
    r.result('Charges directes', direct)
    r.result('Charges indirectes', indirect)
    r.result('Coût de production total', cp, highlight=True)
    r.result('Coût de production unitaire', money(unit))
    return r


@calculator('cout-distribution', 'Coût de distribution', 'BT2', 'Calcul des coûts',
            'Charges directes de distribution + charges du centre distribution imputées.',
            [
                F('lines', 'Éléments du coût de distribution', 'table', required=True, columns=COST_COLUMNS, default=[
                    {'element': 'Commissions des représentants', 'nature': 'direct', 'quantity': '1', 'unit_cost': '450000'},
                    {'element': 'Centre distribution (100 F de CA)', 'nature': 'indirect', 'quantity': '45000', 'unit_cost': '20'},
                ]),
                F('quantity', 'Quantité vendue', 'number', default='0', min=0),
            ])
def calc_cout_distribution(d):
    r = Result()
    r.formulas = ['Coût de distribution = Charges directes de distribution + Charges indirectes du centre distribution']
    direct, indirect, total = _cost_table(r, 'Coût de distribution', d['lines'])
    r.result('Coût de distribution', total, highlight=True)
    if d['quantity']:
        r.result('Coût de distribution unitaire', money(div(total, d['quantity'])))
    return r


@calculator('cout-revient', 'Coût de revient et résultat analytique d\'un produit', 'BT2', 'Calcul des coûts',
            'Coût de production des produits vendus + coût de distribution ; résultat = CA − coût de revient.',
            [
                F('quantity_sold', 'Quantité vendue', 'number', required=True, min=0, default='3500'),
                F('unit_production_cost', 'Coût de production unitaire des produits vendus (CUMP/FIFO)', required=True, min=0, default='1800'),
                F('distribution_cost', 'Coût de distribution', default='1350000', min=0),
                F('unit_price', 'Prix de vente unitaire HT', required=True, min=0, default='2600'),
            ])
def calc_cout_revient(d):
    r = Result()
    cpv = money(d['quantity_sold'] * d['unit_production_cost'])
    cr = cpv + d['distribution_cost']
    ca = money(d['quantity_sold'] * d['unit_price'])
    res = ca - cr
    r.formulas = ['Coût de production des produits vendus = Quantité vendue × Coût unitaire de production',
                  'Coût de revient = Coût de production des produits vendus + Coût de distribution',
                  'Résultat analytique = Chiffre d\'affaires − Coût de revient']
    r.step('Coût de production des produits vendus', f'{fmt(d["quantity_sold"])} × {fmt(d["unit_production_cost"])}', cpv)
    r.step('Coût de revient', f'{fmt(cpv)} + {fmt(d["distribution_cost"])}', cr)
    r.step('Chiffre d\'affaires', f'{fmt(d["quantity_sold"])} × {fmt(d["unit_price"])}', ca)
    r.step('Résultat analytique', f'{fmt(ca)} − {fmt(cr)}', res)
    r.result('Coût de revient', cr)
    if d['quantity_sold']:
        r.result('Coût de revient unitaire', money(div(cr, d['quantity_sold'])))
    r.result('Chiffre d\'affaires', ca)
    r.result('Résultat analytique', res, highlight=True)
    if d['quantity_sold']:
        r.result('Résultat unitaire', money(div(res, d['quantity_sold'])))
    r.interpretation.append('Produit bénéficiaire.' if res >= 0 else 'Produit déficitaire : le prix de vente ne couvre pas le coût de revient.')
    return r


@calculator('resultat-analytique', 'Résultat analytique global et concordance', 'BT2', 'Calcul des coûts',
            'Somme des résultats analytiques par produit et concordance avec le résultat de la comptabilité générale.',
            [
                F('products', 'Produits', 'table', required=True, columns=[
                    F('name', 'Produit', 'text'),
                    F('revenue', 'Chiffre d\'affaires', 'money', min=0),
                    F('cost', 'Coût de revient', 'money', min=0),
                ], default=[{'name': 'Produit P1', 'revenue': '9100000', 'cost': '7650000'},
                            {'name': 'Produit P2', 'revenue': '4500000', 'cost': '4720000'}]),
                F('suppletives', 'Charges supplétives', default='0', min=0),
                F('non_incorporables', 'Charges non incorporables', default='0', min=0),
                F('produits_non_incorpores', 'Produits non incorporés', default='0', min=0),
                F('differences', 'Différences d\'inventaire / d\'arrondi (+ ou −)', default='0'),
            ])
def calc_resultat_analytique(d):
    r = Result()
    rows = []
    total = ZERO
    for p in d['products']:
        res = p['revenue'] - p['cost']
        total += res
        rows.append([p['name'] or '—', p['revenue'], p['cost'], res])
    r.table('Résultats analytiques', ['Produit', 'CA', 'Coût de revient', 'Résultat'], rows, footer=['Total', '', '', total])
    rcg = total + d['suppletives'] - d['non_incorporables'] + d['produits_non_incorpores'] + d['differences']
    r.formulas = ['Résultat analytique = Σ (CA − Coût de revient)',
                  'Résultat CG = Résultat analytique + Charges supplétives − Charges non incorporables + Produits non incorporés ± Différences']
    r.step('Résultat de la comptabilité générale',
           f'{fmt(total)} + {fmt(d["suppletives"])} − {fmt(d["non_incorporables"])} + {fmt(d["produits_non_incorpores"])} + ({fmt(d["differences"])})', rcg)
    r.result('Résultat analytique global', total, highlight=True)
    r.result('Résultat de la comptabilité générale (concordance)', rcg)
    for p in d['products']:
        if p['revenue'] - p['cost'] < 0:
            r.interpretation.append(f'{p["name"]} est déficitaire : analyser son prix de vente et sa structure de coûts.')
    return r


# --------------------------------------------------------------------------------------
# Coûts partiels, seuil de rentabilité, point mort
# --------------------------------------------------------------------------------------

CVP_FIELDS = [
    F('revenue', 'Chiffre d\'affaires HT', required=True, min=0, default='12000000'),
    F('variable_costs', 'Charges variables', required=True, min=0, default='7200000'),
    F('fixed_costs', 'Charges fixes', required=True, min=0, default='3000000'),
]


def _cvp(d):
    mcv = d['revenue'] - d['variable_costs']
    tmcv = div(mcv, d['revenue'], 'chiffre d\'affaires')
    result = mcv - d['fixed_costs']
    return mcv, tmcv, result


@calculator('marge-cout-variable', 'Marge sur coût variable', 'BT2', 'Coûts partiels',
            'Tableau de résultat différentiel : MCV, taux de MCV et résultat.', CVP_FIELDS)
def calc_mcv(d):
    r = Result()
    mcv, tmcv, res = _cvp(d)
    r.formulas = ['MCV = Chiffre d\'affaires − Charges variables', 'Taux de MCV = MCV ÷ CA', 'Résultat = MCV − Charges fixes']
    r.table('Tableau de résultat différentiel', ['Élément', 'Montant', '%'], [
        ['Chiffre d\'affaires', d['revenue'], '100 %'],
        ['− Charges variables', d['variable_costs'], fpct(div(d['variable_costs'], d['revenue']))],
        ['= Marge sur coût variable', mcv, fpct(tmcv)],
        ['− Charges fixes', d['fixed_costs'], fpct(div(d['fixed_costs'], d['revenue']))],
        ['= Résultat', res, fpct(div(res, d['revenue']))],
    ])
    r.result('Marge sur coût variable', mcv, highlight=True)
    r.result('Taux de marge sur coût variable', tmcv * 100, unit='%')
    r.result('Résultat', res)
    r.interpretation.append(f'Chaque tranche de 100 FCFA de chiffre d\'affaires dégage {fmt(tmcv * 100)} FCFA pour couvrir les charges fixes.')
    return r


@calculator('seuil-rentabilite', 'Seuil de rentabilité, marge et indice de sécurité, levier', 'BT2', 'Coûts partiels',
            'Chiffre d\'affaires critique, marge de sécurité, indice de sécurité et levier opérationnel.',
            [*CVP_FIELDS, F('unit_price', 'Prix de vente unitaire (facultatif, pour le seuil en quantité)', default='0', min=0)])
def calc_seuil(d):
    r = Result()
    mcv, tmcv, res = _cvp(d)
    if tmcv <= 0:
        raise CalculationError('La marge sur coût variable est nulle ou négative : aucun seuil de rentabilité n\'existe.', 'variable_costs')
    sr = div(d['fixed_costs'], tmcv)
    ms = d['revenue'] - sr
    isec = div(ms, d['revenue'])
    r.formulas = ['Seuil de rentabilité = Charges fixes ÷ Taux de MCV', 'Marge de sécurité = CA − SR',
                  'Indice de sécurité = Marge de sécurité ÷ CA', 'Levier opérationnel = MCV ÷ Résultat']
    r.step('Taux de MCV', f'{fmt(mcv)} ÷ {fmt(d["revenue"])}', tmcv * 100, unit='%')
    r.step('Seuil de rentabilité', f'{fmt(d["fixed_costs"])} ÷ {fmt(tmcv, 4)}', money(sr))
    r.step('Marge de sécurité', f'{fmt(d["revenue"])} − {fmt(money(sr))}', money(ms))
    r.result('Seuil de rentabilité', money(sr), highlight=True)
    if d['unit_price']:
        r.result('Seuil en quantités', div(sr, d['unit_price']).quantize(Decimal('1')), unit='unités')
    r.result('Marge de sécurité', money(ms))
    r.result('Indice de sécurité', isec * 100, unit='%')
    if res != 0:
        lev = div(mcv, res)
        r.result('Levier opérationnel', lev, unit='')
        r.interpretation.append(f'Levier de {fmt(lev)} : une hausse de 1 % du CA entraîne une hausse d\'environ {fmt(lev)} % du résultat.')
    if ms >= 0:
        r.interpretation.append(f'L\'entreprise est bénéficiaire. Son CA peut baisser de {fpct(isec)} avant d\'atteindre le seuil.')
    else:
        r.interpretation.append('Le CA est inférieur au seuil de rentabilité : l\'entreprise est en perte.')
    return r


MONTHS = ['janvier', 'février', 'mars', 'avril', 'mai', 'juin', 'juillet', 'août', 'septembre', 'octobre', 'novembre', 'décembre']


@calculator('point-mort', 'Point mort (date du seuil)', 'BT2', 'Coûts partiels',
            'Date à laquelle le seuil de rentabilité est atteint, l\'activité étant supposée régulière.',
            [*CVP_FIELDS,
             F('months', 'Durée d\'activité (mois)', 'integer', default='12', min=1, max=12),
             F('start_month', 'Mois de début de l\'exercice', 'integer', default='1', min=1, max=12)])
def calc_point_mort(d):
    r = Result()
    mcv, tmcv, res = _cvp(d)
    if tmcv <= 0:
        raise CalculationError('La marge sur coût variable est nulle ou négative.', 'variable_costs')
    sr = div(d['fixed_costs'], tmcv)
    pm_months = div(sr * d['months'], d['revenue'])
    r.formulas = ['Point mort (en mois) = Seuil de rentabilité ÷ CA × durée d\'activité',
                  'Hypothèse : chiffre d\'affaires réparti uniformément (exprimé en mois de 30 jours)']
    r.step('Seuil de rentabilité', f'{fmt(d["fixed_costs"])} ÷ {fmt(tmcv, 4)}', money(sr))
    r.step('Point mort', f'{fmt(money(sr))} ÷ {fmt(d["revenue"])} × {fmt(d["months"])}', pm_months.quantize(Decimal('0.01')), unit='mois')
    r.result('Seuil de rentabilité', money(sr))
    r.result('Point mort', pm_months.quantize(Decimal('0.01')), unit='mois', highlight=True)
    if pm_months <= d['months']:
        whole = int(pm_months)
        days = int(((pm_months - whole) * 30).to_integral_value())
        month_index = (int(d['start_month']) - 1 + whole) % 12
        day = days
        if days == 0:  # seuil atteint exactement en fin de mois
            day, month_index = 30, (month_index - 1) % 12
        r.result('Date du point mort', f'{day} {MONTHS[month_index]} (≈ {whole} mois et {days} jours)', unit='')
        r.interpretation.append(f'À partir du {day} {MONTHS[month_index]}, chaque vente supplémentaire génère du bénéfice.')
    else:
        r.interpretation.append('Le seuil n\'est pas atteint au cours de l\'exercice : l\'activité est déficitaire.')
    return r


# --------------------------------------------------------------------------------------
# Coûts préétablis et analyse des écarts
# --------------------------------------------------------------------------------------

@calculator('couts-standards', 'Fiche de coût standard', 'BT2', 'Coûts préétablis',
            'Coût standard unitaire et coût préétabli de la production prévue.',
            [
                F('lines', 'Fiche de coût standard (pour 1 unité)', 'table', required=True, columns=[
                    F('element', 'Élément', 'text'),
                    F('quantity', 'Quantité standard', 'number', min=0),
                    F('unit_cost', 'Coût unitaire standard', 'money', min=0),
                ], default=[
                    {'element': 'Matière M (kg)', 'quantity': '2', 'unit_cost': '500'},
                    {'element': 'Main-d\'œuvre directe (h)', 'quantity': '0.5', 'unit_cost': '2400'},
                    {'element': 'Centre atelier (heure machine)', 'quantity': '0.5', 'unit_cost': '1000'},
                ]),
                F('production', 'Production prévue (unités)', 'number', default='4000', min=0),
            ])
def calc_couts_standards(d):
    r = Result()
    rows = []
    unit = ZERO
    for l in d['lines']:
        amount = l['quantity'] * l['unit_cost']
        unit += amount
        rows.append([l['element'] or '—', l['quantity'], l['unit_cost'], money(amount), money(amount * d['production'])])
    r.table('Fiche de coût standard', ['Élément', 'Quantité', 'Coût unitaire', 'Coût pour 1 unité', 'Pour la production prévue'],
            rows, footer=['Total', '', '', money(unit), money(unit * d['production'])])
    r.formulas = ['Coût standard unitaire = Σ (Quantité standard × Coût unitaire standard)',
                  'Coût préétabli de la production = Coût standard unitaire × Production']
    r.result('Coût standard unitaire', money(unit), highlight=True)
    r.result('Coût préétabli de la production', money(unit * d['production']))
    return r


def _label(value: Decimal) -> str:
    if value > 0:
        return 'défavorable'
    if value < 0:
        return 'favorable'
    return 'nul'


@calculator('ecarts', 'Analyse des écarts (matières, MOD, charges indirectes)', 'BT2', 'Coûts préétablis',
            'Écarts sur quantité et sur prix (matières, main-d\'œuvre) et écarts budget / activité / rendement pour un centre.',
            [
                F('actual_production', 'Production réelle (unités)', 'number', required=True, min=0, default='3800'),
                F('mat_std_qty', 'Matière : quantité standard par unité', 'number', default='2', min=0),
                F('mat_std_price', 'Matière : prix standard', default='500', min=0),
                F('mat_real_qty', 'Matière : quantité réelle consommée', 'number', default='7800', min=0),
                F('mat_real_price', 'Matière : prix réel', default='490', min=0),
                F('mod_std_time', 'MOD : temps standard par unité (h)', 'number', default='0.5', min=0),
                F('mod_std_rate', 'MOD : taux horaire standard', default='2400', min=0),
                F('mod_real_time', 'MOD : temps réel (h)', 'number', default='1950', min=0),
                F('mod_real_rate', 'MOD : taux horaire réel', default='2450', min=0),
                F('ci_std_activity_unit', 'Centre : UO standard par unité', 'number', default='0.5', min=0),
                F('ci_normal_activity', 'Centre : activité normale (UO)', 'number', default='2000', min=0),
                F('ci_fixed_budget', 'Centre : charges fixes budgétées', default='1200000', min=0),
                F('ci_variable_unit', 'Centre : coût variable standard par UO', default='400', min=0),
                F('ci_real_activity', 'Centre : activité réelle (UO)', 'number', default='1950', min=0),
                F('ci_real_cost', 'Centre : coût réel du centre', default='2030000', min=0),
            ])
def calc_ecarts(d):
    r = Result()
    p = d['actual_production']
    r.formulas = [
        'Écart global = Coût réel − Coût préétabli de la production réelle',
        'Écart sur quantité = (Quantité réelle − Quantité préétablie) × Prix préétabli',
        'Écart sur prix = (Prix réel − Prix préétabli) × Quantité réelle',
        'Budget flexible BF(A) = Charges fixes + Coût variable unitaire × A',
        'Écart sur budget = Coût réel − BF(activité réelle)',
        'Écart sur activité = BF(activité réelle) − Coût standard de l\'UO × activité réelle',
        'Écart sur rendement = (Activité réelle − Activité préétablie) × Coût standard de l\'UO',
        'Un écart positif (coût réel > coût préétabli) est défavorable.']
    rows = []
    # Matières
    qs = d['mat_std_qty'] * p
    eq = (d['mat_real_qty'] - qs) * d['mat_std_price']
    ep = (d['mat_real_price'] - d['mat_std_price']) * d['mat_real_qty']
    eg_m = d['mat_real_qty'] * d['mat_real_price'] - qs * d['mat_std_price']
    rows += [['Matières', 'Quantité', money(eq), _label(eq)], ['Matières', 'Prix', money(ep), _label(ep)],
             ['Matières', 'Global', money(eg_m), _label(eg_m)]]
    r.step('Matières — quantité préétablie', f'{fmt(d["mat_std_qty"])} × {fmt(p)}', qs, unit='')
    # MOD
    ts = d['mod_std_time'] * p
    et = (d['mod_real_time'] - ts) * d['mod_std_rate']
    er = (d['mod_real_rate'] - d['mod_std_rate']) * d['mod_real_time']
    eg_mod = d['mod_real_time'] * d['mod_real_rate'] - ts * d['mod_std_rate']
    rows += [['MOD', 'Temps (rendement)', money(et), _label(et)], ['MOD', 'Taux', money(er), _label(er)],
             ['MOD', 'Global', money(eg_mod), _label(eg_mod)]]
    r.step('MOD — temps préétabli', f'{fmt(d["mod_std_time"])} × {fmt(p)}', ts, unit='h')
    # Charges indirectes
    an = d['ci_normal_activity']
    if an > 0:
        cs = div(d['ci_fixed_budget'], an) + d['ci_variable_unit']
        ar = d['ci_real_activity']
        ap = d['ci_std_activity_unit'] * p
        bf = d['ci_fixed_budget'] + d['ci_variable_unit'] * ar
        eb = d['ci_real_cost'] - bf
        ea = bf - cs * ar
        erd = (ar - ap) * cs
        eg_ci = d['ci_real_cost'] - ap * cs
        r.step('Coût standard de l\'UO', f'{fmt(d["ci_fixed_budget"])} ÷ {fmt(an)} + {fmt(d["ci_variable_unit"])}', money(cs))
        r.step('Activité préétablie', f'{fmt(d["ci_std_activity_unit"])} × {fmt(p)}', ap, unit='UO')
        r.step('Budget flexible', f'{fmt(d["ci_fixed_budget"])} + {fmt(d["ci_variable_unit"])} × {fmt(ar)}', money(bf))
        rows += [['Charges indirectes', 'Budget', money(eb), _label(eb)], ['Charges indirectes', 'Activité', money(ea), _label(ea)],
                 ['Charges indirectes', 'Rendement', money(erd), _label(erd)], ['Charges indirectes', 'Global', money(eg_ci), _label(eg_ci)]]
        r.result('Écart global charges indirectes', money(eg_ci))
    else:
        eg_ci = ZERO
    r.table('Analyse des écarts', ['Élément', 'Écart', 'Montant', 'Sens'], rows)
    r.result('Écart global matières', money(eg_m))
    r.result('Écart global MOD', money(eg_mod))
    total = eg_m + eg_mod + eg_ci
    r.result('Écart global total', money(total), highlight=True)
    r.interpretation.append(f'Écart total {_label(total)} de {fcfa(abs(money(total)))}. Un écart sur quantité ou temps relève '
                            'en général de la production ; un écart sur prix ou taux relève des achats ou de la politique salariale.')
    return r
