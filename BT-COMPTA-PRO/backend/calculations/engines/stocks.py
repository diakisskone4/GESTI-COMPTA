"""Fiches de stock : premier entré premier sorti (PEPS / FIFO) et coût unitaire moyen pondéré (CUMP)."""
from collections import deque
from decimal import Decimal

from .base import ZERO, CalculationError, F, Result, calculator, div, fcfa, fmt, money, options

MOVEMENT_COLUMNS = [
    F('date', 'Date', 'text'),
    F('label', 'Libellé', 'text'),
    F('kind', 'Type', 'select', options=options(('in', 'Entrée'), ('out', 'Sortie'))),
    F('quantity', 'Quantité', 'number', min=0),
    F('unit_cost', 'Coût unitaire (entrées)', 'money', min=0),
]

DEFAULT_MOVES = [
    {'date': '05/01', 'label': 'Achat', 'kind': 'in', 'quantity': '200', 'unit_cost': '1100'},
    {'date': '10/01', 'label': 'Vente', 'kind': 'out', 'quantity': '250', 'unit_cost': ''},
    {'date': '18/01', 'label': 'Achat', 'kind': 'in', 'quantity': '300', 'unit_cost': '1200'},
    {'date': '25/01', 'label': 'Vente', 'kind': 'out', 'quantity': '180', 'unit_cost': ''},
]

COMMON_FIELDS = [
    F('initial_qty', 'Stock initial — quantité', 'number', default='100', min=0),
    F('initial_cost', 'Stock initial — coût unitaire', default='1000', min=0),
    F('movements', 'Mouvements de la période', 'table', required=True, columns=MOVEMENT_COLUMNS, default=DEFAULT_MOVES),
]

COLUMNS = ['Date', 'Libellé', 'Entrée Q', 'Entrée PU', 'Entrée montant', 'Sortie Q', 'Sortie PU', 'Sortie montant', 'Stock Q', 'Stock valeur']


@calculator('fifo', 'Fiche de stock FIFO (PEPS)', 'BT1', 'Stocks',
            'Valorisation des sorties selon la méthode « premier entré, premier sorti ».', COMMON_FIELDS)
def calc_fifo(d):
    r = Result()
    r.formulas = ['Les sorties sont valorisées au coût des lots les plus anciens encore en stock.',
                  'Stock final = lots restants × leur coût d\'entrée']
    lots: deque[list[Decimal]] = deque()
    if d['initial_qty'] > 0:
        lots.append([d['initial_qty'], d['initial_cost']])
    stock_value = lambda: sum((q * c for q, c in lots), ZERO)  # noqa: E731
    stock_qty = lambda: sum((q for q, _ in lots), ZERO)  # noqa: E731
    rows = [['', 'Stock initial', '', '', '', '', '', '', d['initial_qty'], money(stock_value())]]
    total_out = ZERO
    total_out_qty = ZERO
    for i, m in enumerate(d['movements'], start=1):
        q = m['quantity']
        if q <= 0:
            raise CalculationError(f'Mouvement {i} : la quantité doit être positive.', 'movements')
        if m['kind'] == 'in':
            lots.append([q, m['unit_cost']])
            rows.append([m['date'], m['label'] or 'Entrée', q, m['unit_cost'], money(q * m['unit_cost']), '', '', '',
                         stock_qty(), money(stock_value())])
            continue
        if q > stock_qty():
            raise CalculationError(f'Mouvement {i} ({m["date"]}) : sortie de {fmt(q)} supérieure au stock disponible ({fmt(stock_qty())}).', 'movements')
        remaining = q
        first = True
        while remaining > 0:
            lot = lots[0]
            take = min(lot[0], remaining)
            amount = money(take * lot[1])
            lot[0] -= take
            remaining -= take
            if lot[0] == 0:
                lots.popleft()
            total_out += amount
            total_out_qty += take
            rows.append([m['date'] if first else '', (m['label'] or 'Sortie') if first else '↳ lot suivant', '', '', '',
                         take, lot[1], amount, stock_qty(), money(stock_value())])
            first = False
    r.table('Fiche de stock — FIFO', COLUMNS, rows)
    r.result('Quantité sortie', total_out_qty, unit='unités')
    r.result('Coût des sorties', total_out)
    r.result('Stock final (quantité)', stock_qty(), unit='unités')
    r.result('Stock final (valeur)', money(stock_value()), highlight=True)
    r.interpretation.append('En période de hausse des prix, le FIFO valorise le stock final aux prix les plus récents '
                            '(stock élevé) et les sorties aux prix anciens (coût des ventes plus faible).')
    return r


@calculator('cump', 'Fiche de stock CUMP', 'BT1', 'Stocks',
            'Valorisation au coût unitaire moyen pondéré, de fin de période ou après chaque entrée.',
            [F('mode', 'Méthode', 'select', default='mobile',
               options=options(('mobile', 'CUMP après chaque entrée'), ('periode', 'CUMP de fin de période'))),
             *COMMON_FIELDS])
def calc_cump(d):
    r = Result()
    qty = d['initial_qty']
    value = qty * d['initial_cost']
    rows = [['', 'Stock initial', '', '', '', '', '', '', qty, money(value)]]
    total_out = ZERO
    if d['mode'] == 'periode':
        in_q = sum((m['quantity'] for m in d['movements'] if m['kind'] == 'in'), ZERO)
        in_v = sum((m['quantity'] * m['unit_cost'] for m in d['movements'] if m['kind'] == 'in'), ZERO)
        cump = div(value + in_v, qty + in_q, 'stock initial + entrées (quantité)')
        r.formulas = ['CUMP = (Valeur du stock initial + Valeur des entrées) ÷ (Quantité initiale + Quantités entrées)',
                      'Toutes les sorties sont valorisées à ce CUMP unique.']
        r.step('CUMP de la période', f'({fmt(value)} + {fmt(in_v)}) ÷ ({fmt(qty)} + {fmt(in_q)})', money(cump))
    else:
        cump = div(value, qty, 'stock') if qty else ZERO
        r.formulas = ['Après chaque entrée : CUMP = (Valeur du stock + Valeur de l\'entrée) ÷ (Quantité en stock + Quantité entrée)',
                      'Les sorties sont valorisées au dernier CUMP calculé.']
    for i, m in enumerate(d['movements'], start=1):
        q = m['quantity']
        if q <= 0:
            raise CalculationError(f'Mouvement {i} : la quantité doit être positive.', 'movements')
        if m['kind'] == 'in':
            amount = q * m['unit_cost']
            qty += q
            value += amount
            if d['mode'] == 'mobile':
                cump = div(value, qty, 'stock')
                r.step(f'CUMP après {m["label"] or "entrée"} du {m["date"]}', f'{fmt(money(value))} ÷ {fmt(qty)}', money(cump))
            rows.append([m['date'], m['label'] or 'Entrée', q, m['unit_cost'], money(amount), '', '', '', qty, money(value)])
        else:
            if q > qty:
                raise CalculationError(f'Mouvement {i} ({m["date"]}) : sortie de {fmt(q)} supérieure au stock disponible ({fmt(qty)}).', 'movements')
            amount = money(q * cump)
            qty -= q
            value = value - amount if qty else ZERO
            total_out += amount
            rows.append([m['date'], m['label'] or 'Sortie', '', '', '', q, money(cump), amount, qty, money(value)])
    if d['mode'] == 'periode':
        value = money(qty * cump)
        rows[-1][-1] = value
    r.table('Fiche de stock — CUMP', COLUMNS, rows)
    r.result('CUMP final', money(cump))
    r.result('Coût des sorties', total_out)
    r.result('Stock final (quantité)', qty, unit='unités')
    r.result('Stock final (valeur)', money(value), highlight=True)
    r.interpretation.append('Le CUMP lisse les variations de prix : les sorties et le stock final sont valorisés à un coût moyen. '
                            f'Valeur du stock final : {fcfa(money(value))}.')
    return r
