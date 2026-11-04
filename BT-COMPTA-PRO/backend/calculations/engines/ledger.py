"""Générateurs de journal, grand livre et balance à partir d'une liste d'écritures."""
from collections import OrderedDict, defaultdict

from .base import ZERO, CalculationError, F, Result, calculator, fcfa, money


def account_label(code: str) -> str:
    try:
        from accounting.data.syscohada import label_for
        return label_for(code)
    except Exception:  # pragma: no cover - données indisponibles
        return ''


LINE_COLUMNS = [
    F('date', 'Date', 'text'),
    F('piece', 'N° pièce', 'text'),
    F('account', 'Compte', 'text'),
    F('label', 'Libellé', 'text'),
    F('debit', 'Débit', 'money', min=0),
    F('credit', 'Crédit', 'money', min=0),
]

DEFAULT_LINES = [
    {'date': '02/01', 'piece': 'FA001', 'account': '601', 'label': 'Achat de marchandises', 'debit': '500000', 'credit': ''},
    {'date': '02/01', 'piece': 'FA001', 'account': '4452', 'label': 'TVA récupérable', 'debit': '90000', 'credit': ''},
    {'date': '02/01', 'piece': 'FA001', 'account': '401', 'label': 'Fournisseur Diallo', 'debit': '', 'credit': '590000'},
    {'date': '05/01', 'piece': 'FV001', 'account': '411', 'label': 'Client Traoré', 'debit': '826000', 'credit': ''},
    {'date': '05/01', 'piece': 'FV001', 'account': '701', 'label': 'Vente de marchandises', 'debit': '', 'credit': '700000'},
    {'date': '05/01', 'piece': 'FV001', 'account': '4431', 'label': 'TVA facturée', 'debit': '', 'credit': '126000'},
    {'date': '10/01', 'piece': 'BQ001', 'account': '521', 'label': 'Règlement client Traoré', 'debit': '826000', 'credit': ''},
    {'date': '10/01', 'piece': 'BQ001', 'account': '411', 'label': 'Règlement client Traoré', 'debit': '', 'credit': '826000'},
]

FIELDS = [F('lines', 'Lignes d\'écritures', 'table', required=True, columns=LINE_COLUMNS, default=DEFAULT_LINES)]


def _validate(lines):
    for i, line in enumerate(lines, start=1):
        if not line['account']:
            raise CalculationError(f'Ligne {i} : le numéro de compte est obligatoire.', 'lines')
        if not line['account'].isdigit():
            raise CalculationError(f'Ligne {i} : le compte « {line["account"]} » doit être numérique.', 'lines')
        if line['debit'] and line['credit']:
            raise CalculationError(f'Ligne {i} : une ligne ne peut pas être à la fois au débit et au crédit.', 'lines')
        if not line['debit'] and not line['credit']:
            raise CalculationError(f'Ligne {i} : saisir un montant au débit ou au crédit.', 'lines')


def _pieces(lines):
    pieces = OrderedDict()
    for line in lines:
        pieces.setdefault(line['piece'] or '(sans pièce)', []).append(line)
    return pieces


@calculator('journal', 'Générateur de journal', 'BT1', 'Documents comptables',
            'Présente les écritures au journal et contrôle l\'égalité débit = crédit de chaque pièce.', FIELDS)
def calc_journal(d):
    r = Result()
    lines = d['lines']
    _validate(lines)
    r.formulas = ['Partie double : pour chaque écriture, Σ Débits = Σ Crédits']
    rows = []
    total_d = total_c = ZERO
    unbalanced = []
    for piece, plines in _pieces(lines).items():
        pd = sum((l['debit'] for l in plines), ZERO)
        pc = sum((l['credit'] for l in plines), ZERO)
        if money(pd) != money(pc):
            unbalanced.append(f'{piece} (débit {fcfa(pd)} ≠ crédit {fcfa(pc)})')
        for l in plines:
            rows.append([l['date'], piece, l['account'] if l['debit'] else '', '' if l['debit'] else l['account'],
                         l['label'] or account_label(l['account']), l['debit'] or '', l['credit'] or ''])
        total_d += pd
        total_c += pc
    r.table('Journal', ['Date', 'Pièce', 'Compte débité', 'Compte crédité', 'Libellé', 'Débit', 'Crédit'], rows,
            footer=['', '', '', '', 'TOTAUX', total_d, total_c])
    r.result('Total débit', total_d)
    r.result('Total crédit', total_c)
    r.result('Nombre d\'écritures', str(len(_pieces(lines))), unit='')
    r.result('Contrôle', 'Journal équilibré ✔' if not unbalanced and money(total_d) == money(total_c) else 'Déséquilibre ✖', unit='', highlight=True)
    for u in unbalanced:
        r.warnings.append(f'Écriture déséquilibrée : {u}')
    return r


def _accounts(lines):
    accounts = defaultdict(list)
    for line in lines:
        accounts[line['account']].append(line)
    return OrderedDict(sorted(accounts.items()))


@calculator('grand-livre', 'Générateur de grand livre', 'BT1', 'Documents comptables',
            'Reporte les écritures par compte avec le solde progressif.', FIELDS)
def calc_grand_livre(d):
    r = Result()
    lines = d['lines']
    _validate(lines)
    r.formulas = ['Solde d\'un compte = Σ Débits − Σ Crédits (débiteur si > 0, créditeur si < 0)']
    for account, alines in _accounts(lines).items():
        balance = ZERO
        rows = []
        td = tc = ZERO
        for l in alines:
            balance += l['debit'] - l['credit']
            td += l['debit']
            tc += l['credit']
            rows.append([l['date'], l['piece'], l['label'], l['debit'] or '', l['credit'] or '',
                         f'{money(abs(balance))} {"D" if balance > 0 else "C" if balance < 0 else ""}'.strip()])
        label = account_label(account)
        r.table(f'Compte {account}{" — " + label if label else ""}', ['Date', 'Pièce', 'Libellé', 'Débit', 'Crédit', 'Solde'],
                rows, footer=['', '', 'Totaux', td, tc, f'{money(abs(balance))} {"D" if balance > 0 else "C" if balance < 0 else ""}'.strip()])
    r.result('Nombre de comptes mouvementés', str(len(_accounts(lines))), unit='', highlight=True)
    return r


@calculator('balance', 'Générateur de balance', 'BT1', 'Documents comptables',
            'Balance générale : totaux et soldes de chaque compte, contrôle des égalités.', FIELDS)
def calc_balance(d):
    r = Result()
    lines = d['lines']
    _validate(lines)
    r.formulas = ['Σ Mouvements débit = Σ Mouvements crédit', 'Σ Soldes débiteurs = Σ Soldes créditeurs']
    rows = []
    td = tc = sd = sc = ZERO
    for account, alines in _accounts(lines).items():
        deb = sum((l['debit'] for l in alines), ZERO)
        cre = sum((l['credit'] for l in alines), ZERO)
        solde = deb - cre
        rows.append([account, account_label(account), deb, cre, solde if solde > 0 else '', -solde if solde < 0 else ''])
        td += deb
        tc += cre
        sd += max(solde, ZERO)
        sc += max(-solde, ZERO)
    r.table('Balance générale', ['Compte', 'Intitulé', 'Mouvements débit', 'Mouvements crédit', 'Solde débiteur', 'Solde créditeur'],
            rows, footer=['', 'TOTAUX', td, tc, sd, sc])
    r.result('Total mouvements débit', td)
    r.result('Total mouvements crédit', tc)
    r.result('Total soldes débiteurs', sd)
    r.result('Total soldes créditeurs', sc)
    ok = money(td) == money(tc) and money(sd) == money(sc)
    r.result('Contrôle', 'Balance équilibrée ✔' if ok else 'Balance déséquilibrée ✖', unit='', highlight=True)
    if not ok:
        r.warnings.append('La balance ne s\'équilibre pas : une écriture est déséquilibrée ou mal reportée.')
    return r
