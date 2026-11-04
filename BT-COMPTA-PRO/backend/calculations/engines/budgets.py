"""Calculatrices BT2 — budgets et gestion prévisionnelle."""
from .base import TVA_HELP, ZERO, CalculationError, F, Result, calculator, fcfa, fmt, money, pct


@calculator('budget-ventes', 'Budget des ventes', 'BT2', 'Budgets',
            'Chiffre d\'affaires HT, TVA et TTC prévisionnels par période.',
            [
                F('periods', 'Prévisions', 'table', required=True, columns=[
                    F('period', 'Période', 'text'),
                    F('quantity', 'Quantités prévues', 'number', min=0),
                    F('unit_price', 'Prix unitaire HT', 'money', min=0),
                ], default=[{'period': 'Janvier', 'quantity': '1200', 'unit_price': '2500'},
                            {'period': 'Février', 'quantity': '1350', 'unit_price': '2500'},
                            {'period': 'Mars', 'quantity': '1500', 'unit_price': '2600'}]),
                F('vat', 'Taux de TVA (%)', 'percent', default='18', min=0, max=100, help=TVA_HELP),
            ])
def calc_budget_ventes(d):
    r = Result()
    r.formulas = ['CA HT = Quantités × Prix unitaire HT', 'TVA collectée = CA HT × taux', 'CA TTC = CA HT + TVA']
    rows = []
    th = tt = ttc = q = ZERO
    for p in d['periods']:
        ht = money(p['quantity'] * p['unit_price'])
        tva = money(ht * pct(d['vat']))
        rows.append([p['period'], p['quantity'], p['unit_price'], ht, tva, ht + tva])
        th += ht; tt += tva; ttc += ht + tva; q += p['quantity']
    r.table('Budget des ventes', ['Période', 'Quantités', 'Prix HT', 'CA HT', 'TVA', 'CA TTC'], rows, footer=['Total', q, '', th, tt, ttc])
    r.result('Quantités totales', q, unit='unités')
    r.result('Chiffre d\'affaires HT', th, highlight=True)
    r.result('TVA collectée', tt)
    r.result('Chiffre d\'affaires TTC (base des encaissements)', ttc)
    return r


@calculator('budget-production', 'Budget de production', 'BT2', 'Budgets',
            'Quantités à produire = ventes prévues + stock final souhaité − stock initial.',
            [
                F('initial_stock', 'Stock initial de produits finis', 'number', default='300', min=0),
                F('periods', 'Prévisions', 'table', required=True, columns=[
                    F('period', 'Période', 'text'),
                    F('sales', 'Ventes prévues (quantités)', 'number', min=0),
                    F('final_stock', 'Stock final souhaité', 'number', min=0),
                ], default=[{'period': 'Janvier', 'sales': '1200', 'final_stock': '400'},
                            {'period': 'Février', 'sales': '1350', 'final_stock': '450'},
                            {'period': 'Mars', 'sales': '1500', 'final_stock': '350'}]),
                F('unit_cost', 'Coût de production unitaire prévu (facultatif)', default='0', min=0),
            ])
def calc_budget_production(d):
    r = Result()
    r.formulas = ['Production = Ventes prévues + Stock final souhaité − Stock initial',
                  'Le stock final d\'une période devient le stock initial de la suivante.']
    stock = d['initial_stock']
    rows = []
    total = ZERO
    for p in d['periods']:
        prod = p['sales'] + p['final_stock'] - stock
        if prod < 0:
            r.warnings.append(f'{p["period"]} : production négative ({fmt(prod)}) — le stock initial couvre déjà les besoins ; production ramenée à 0.')
            prod = ZERO
        rows.append([p['period'], stock, p['sales'], p['final_stock'], prod, money(prod * d['unit_cost']) if d['unit_cost'] else ''])
        total += prod
        stock = p['final_stock']
    r.table('Budget de production', ['Période', 'Stock initial', 'Ventes', 'Stock final', 'Production', 'Coût'], rows,
            footer=['Total', '', '', '', total, money(total * d['unit_cost']) if d['unit_cost'] else ''])
    r.result('Production totale', total, unit='unités', highlight=True)
    if d['unit_cost']:
        r.result('Coût de production prévisionnel', money(total * d['unit_cost']))
    return r


@calculator('budget-achats', 'Budget des approvisionnements (achats)', 'BT2', 'Budgets',
            'Achats = consommations prévues + stock final souhaité − stock initial, valorisés au prix prévu.',
            [
                F('initial_stock', 'Stock initial de matières (quantité)', 'number', default='1500', min=0),
                F('unit_price', 'Prix d\'achat unitaire HT prévu', required=True, min=0, default='450'),
                F('periods', 'Prévisions', 'table', required=True, columns=[
                    F('period', 'Période', 'text'),
                    F('needs', 'Consommations prévues', 'number', min=0),
                    F('final_stock', 'Stock final souhaité (stock de sécurité inclus)', 'number', min=0),
                ], default=[{'period': 'Janvier', 'needs': '2600', 'final_stock': '1200'},
                            {'period': 'Février', 'needs': '2800', 'final_stock': '1200'},
                            {'period': 'Mars', 'needs': '3100', 'final_stock': '1000'}]),
                F('vat', 'Taux de TVA (%)', 'percent', default='18', min=0, max=100, help=TVA_HELP),
            ])
def calc_budget_achats(d):
    r = Result()
    r.formulas = ['Achats (quantités) = Consommations + Stock final souhaité − Stock initial',
                  'Achats HT = Quantités × Prix unitaire', 'Achats TTC = Achats HT × (1 + taux de TVA)']
    stock = d['initial_stock']
    rows = []
    tq = th = tttc = ZERO
    for p in d['periods']:
        q = max(ZERO, p['needs'] + p['final_stock'] - stock)
        ht = money(q * d['unit_price'])
        ttc = money(ht * (1 + pct(d['vat'])))
        rows.append([p['period'], stock, p['needs'], p['final_stock'], q, ht, ttc])
        tq += q; th += ht; tttc += ttc
        stock = p['final_stock']
    r.table('Budget des achats', ['Période', 'Stock initial', 'Consommations', 'Stock final', 'Achats (Q)', 'Achats HT', 'Achats TTC'],
            rows, footer=['Total', '', '', '', tq, th, tttc])
    r.result('Quantités à acheter', tq, unit='unités')
    r.result('Achats HT', th, highlight=True)
    r.result('Achats TTC (base des décaissements)', tttc)
    return r


@calculator('budget-tresorerie', 'Budget de trésorerie', 'BT2', 'Budgets',
            'Encaissements, décaissements, soldes mensuels et trésorerie de fin de période.',
            [
                F('initial_cash', 'Trésorerie initiale', default='500000'),
                F('periods', 'Flux prévisionnels', 'table', required=True, columns=[
                    F('period', 'Période', 'text'),
                    F('receipts', 'Encaissements', 'money', min=0),
                    F('payments', 'Décaissements', 'money', min=0),
                ], default=[{'period': 'Janvier', 'receipts': '3200000', 'payments': '3600000'},
                            {'period': 'Février', 'receipts': '3500000', 'payments': '3300000'},
                            {'period': 'Mars', 'receipts': '3900000', 'payments': '4400000'}]),
            ])
def calc_budget_tresorerie(d):
    r = Result()
    r.formulas = ['Solde du mois = Encaissements − Décaissements', 'Trésorerie fin = Trésorerie début + Solde du mois']
    cash = d['initial_cash']
    rows = []
    te = td = ZERO
    deficits = []
    for p in d['periods']:
        solde = p['receipts'] - p['payments']
        start = cash
        cash += solde
        te += p['receipts']; td += p['payments']
        rows.append([p['period'], start, p['receipts'], p['payments'], solde, cash])
        if cash < 0:
            deficits.append(f'{p["period"]} ({fcfa(cash)})')
    r.table('Budget de trésorerie', ['Période', 'Trésorerie début', 'Encaissements', 'Décaissements', 'Solde du mois', 'Trésorerie fin'],
            rows, footer=['Total', d['initial_cash'], te, td, te - td, cash])
    r.result('Total des encaissements', te)
    r.result('Total des décaissements', td)
    r.result('Trésorerie finale', cash, highlight=True)
    if deficits:
        r.interpretation.append('Trésorerie négative en : ' + ', '.join(deficits) +
                                '. Prévoir un financement à court terme (découvert, escompte d\'effets) ou décaler des décaissements.')
    else:
        r.interpretation.append('La trésorerie reste positive sur toute la période : excédents éventuellement plaçables.')
    return r


@calculator('controle-budgetaire', 'Contrôle budgétaire', 'BT2', 'Budgets',
            'Comparaison réalisations / prévisions et taux de réalisation.',
            [
                F('lines', 'Postes', 'table', required=True, columns=[
                    F('item', 'Poste', 'text'),
                    F('kind', 'Nature', 'select', options=[{'value': 'produit', 'label': 'Produit'}, {'value': 'charge', 'label': 'Charge'}]),
                    F('budget', 'Prévision', 'money'),
                    F('actual', 'Réalisation', 'money'),
                ], default=[{'item': 'Ventes', 'kind': 'produit', 'budget': '12000000', 'actual': '11400000'},
                            {'item': 'Achats consommés', 'kind': 'charge', 'budget': '6500000', 'actual': '6300000'}]),
            ])
def calc_controle_budgetaire(d):
    r = Result()
    r.formulas = ['Écart = Réalisation − Prévision', 'Taux de réalisation = Réalisation ÷ Prévision',
                  'Produit : écart positif favorable ; Charge : écart positif défavorable']
    rows = []
    for l in d['lines']:
        e = l['actual'] - l['budget']
        if l['budget'] == 0:
            raise CalculationError(f'{l["item"]} : la prévision ne peut pas être nulle.', 'lines')
        favorable = (e >= 0) if l['kind'] == 'produit' else (e <= 0)
        rows.append([l['item'], l['budget'], l['actual'], e, f'{fmt(l["actual"] / l["budget"] * 100)} %', 'Favorable' if favorable else 'Défavorable'])
    r.table('Contrôle budgétaire', ['Poste', 'Prévision', 'Réalisation', 'Écart', 'Taux de réalisation', 'Appréciation'], rows)
    r.result('Postes analysés', str(len(rows)), unit='', highlight=True)
    return r
