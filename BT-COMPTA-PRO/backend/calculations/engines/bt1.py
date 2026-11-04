"""Calculatrices BT1 — comptabilité générale (SYSCOHADA révisé).

Les numéros de comptes utilisés suivent le plan comptable SYSCOHADA révisé ; ils sont
listés dans accounting/data/syscohada.py avec leur statut de vérification.
"""
from datetime import date
from decimal import Decimal

from .base import (TVA_HELP, ZERO, CalculationError, F, Result, calculator, div, fcfa, fmt, fpct, money,
                   options, pct)

# --------------------------------------------------------------------------------------
# 1. HT / TVA / TTC
# --------------------------------------------------------------------------------------


@calculator(
    'tva', 'Calculatrice HT, TVA et TTC', 'BT1', 'Factures et TVA',
    'Passer du hors taxes au toutes taxes comprises (ou l\'inverse) et calculer la TVA.',
    [
        F('mode', 'Montant connu', 'select', default='ht', options=options(('ht', 'Montant hors taxes (HT)'), ('ttc', 'Montant toutes taxes comprises (TTC)'))),
        F('amount', 'Montant', required=True, min=0),
        F('rate', 'Taux de TVA (%)', 'percent', default='18', min=0, max=100, help=TVA_HELP),
    ],
)
def calc_tva(d):
    r = Result()
    t = pct(d['rate'])
    if d['mode'] == 'ht':
        ht = d['amount']
        tva = ht * t
        ttc = ht + tva
        r.formulas = ['TVA = HT × taux', 'TTC = HT + TVA = HT × (1 + taux)']
        r.step('TVA', f'{fmt(ht)} × {fmt(d["rate"])} %', tva)
        r.step('TTC', f'{fmt(ht)} + {fmt(tva)}', ttc)
    else:
        ttc = d['amount']
        ht = div(ttc, 1 + t, 'coefficient (1 + taux)')
        tva = ttc - ht
        r.formulas = ['HT = TTC ÷ (1 + taux)', 'TVA = TTC − HT']
        r.step('HT', f'{fmt(ttc)} ÷ {fmt(1 + t, 4)}', ht)
        r.step('TVA', f'{fmt(ttc)} − {fmt(ht)}', tva)
    r.result('Montant HT', money(ht))
    r.result('TVA', money(tva))
    r.result('Montant TTC', money(ttc), highlight=True)
    r.interpretation.append(
        f'Sur un montant TTC de {fcfa(money(ttc))}, {fcfa(money(tva))} représentent la TVA collectée pour le compte de '
        'l\'État : elle n\'est ni une charge ni un produit pour l\'entreprise assujettie.')
    return r


# --------------------------------------------------------------------------------------
# 2. Réductions commerciales
# --------------------------------------------------------------------------------------

@calculator(
    'reductions', 'Réductions commerciales en cascade', 'BT1', 'Factures et TVA',
    'Calcul du net commercial après remise, rabais et ristourne (appliqués successivement).',
    [
        F('gross', 'Montant brut HT', required=True, min=0),
        F('remise', 'Remise (%)', 'percent', default='0', min=0, max=100),
        F('rabais', 'Rabais (%)', 'percent', default='0', min=0, max=100),
        F('ristourne', 'Ristourne (%)', 'percent', default='0', min=0, max=100),
    ],
)
def calc_reductions(d):
    r = Result()
    r.formulas = ['Chaque réduction s\'applique sur le net précédent : Net = Base × (1 − taux)',
                  'Net commercial = Brut × (1 − r1) × (1 − r2) × (1 − r3)']
    base = d['gross']
    total = ZERO
    rows = [['Montant brut', '', base]]
    for key, label in (('remise', 'Remise'), ('rabais', 'Rabais'), ('ristourne', 'Ristourne')):
        if d[key] > 0:
            red = money(base * pct(d[key]))
            r.step(label, f'{fmt(base)} × {fmt(d[key])} %', red)
            base -= red
            total += red
            rows.append([f'− {label} {fmt(d[key])} %', red, base])
    r.table('Cascade des réductions', ['Élément', 'Réduction', 'Net'], rows)
    r.result('Total des réductions', total)
    r.result('Net commercial HT', base, highlight=True)
    if d['gross'] > 0:
        global_rate = total / d['gross']
        r.result('Taux de réduction global', global_rate * 100, unit='%')
        r.interpretation.append(
            f'Les réductions successives ne s\'additionnent pas : le taux global est de {fpct(global_rate)}, '
            'inférieur à la somme des taux car chaque réduction porte sur un montant déjà diminué.')
    r.interpretation.append('Les réductions commerciales figurant sur la facture ne sont pas comptabilisées : '
                            'on enregistre directement le net commercial.')
    return r


# --------------------------------------------------------------------------------------
# 3. Escompte
# --------------------------------------------------------------------------------------

@calculator(
    'escompte', 'Escompte de règlement', 'BT1', 'Factures et TVA',
    'Réduction financière accordée pour paiement anticipé : net financier, TVA et TTC.',
    [
        F('net_commercial', 'Net commercial HT', required=True, min=0),
        F('rate', 'Taux d\'escompte (%)', 'percent', required=True, min=0, max=100),
        F('vat', 'Taux de TVA (%)', 'percent', default='18', min=0, max=100, help=TVA_HELP),
    ],
)
def calc_escompte(d):
    r = Result()
    nc = d['net_commercial']
    esc = money(nc * pct(d['rate']))
    nf = nc - esc
    tva = money(nf * pct(d['vat']))
    ttc = nf + tva
    r.formulas = ['Escompte = Net commercial × taux d\'escompte', 'Net financier = Net commercial − Escompte',
                  'TVA = Net financier × taux de TVA', 'Net à payer = Net financier + TVA']
    r.step('Escompte', f'{fmt(nc)} × {fmt(d["rate"])} %', esc)
    r.step('Net financier', f'{fmt(nc)} − {fmt(esc)}', nf)
    r.step('TVA', f'{fmt(nf)} × {fmt(d["vat"])} %', tva)
    r.step('Net à payer TTC', f'{fmt(nf)} + {fmt(tva)}', ttc)
    r.result('Escompte', esc)
    r.result('Net financier', nf)
    r.result('TVA', tva)
    r.result('Net à payer', ttc, highlight=True)
    r.entry('601', 'Achats de marchandises', debit=nc, group='Chez l\'acheteur')
    r.entry('4452', 'TVA récupérable sur achats', debit=tva, group='Chez l\'acheteur')
    r.entry('401', 'Fournisseurs', credit=ttc, group='Chez l\'acheteur')
    r.entry('773', 'Escomptes obtenus', credit=esc, group='Chez l\'acheteur')
    r.entry('411', 'Clients', debit=ttc, group='Chez le vendeur')
    r.entry('673', 'Escomptes accordés', debit=esc, group='Chez le vendeur')
    r.entry('701', 'Ventes de marchandises', credit=nc, group='Chez le vendeur')
    r.entry('4431', 'TVA facturée sur ventes', credit=tva, group='Chez le vendeur')
    r.interpretation.append('L\'escompte est une réduction financière : il est comptabilisé en produit financier '
                            '(773) chez l\'acheteur et en charge financière (673) chez le vendeur. La TVA est calculée sur le net financier.')
    return r


# --------------------------------------------------------------------------------------
# 4. Facture complète
# --------------------------------------------------------------------------------------

@calculator(
    'facture', 'Facture de doit complète', 'BT1', 'Factures et TVA',
    'Établit une facture : lignes d\'articles, réductions, escompte, port, emballages consignés, TVA, '
    'et génère les écritures chez l\'acheteur et le vendeur.',
    [
        F('lines', 'Articles', 'table', required=True, columns=[
            F('designation', 'Désignation', 'text'),
            F('quantity', 'Quantité', 'number', min=0),
            F('unit_price', 'Prix unitaire HT', 'money', min=0),
        ], default=[{'designation': 'Marchandise A', 'quantity': '10', 'unit_price': '5000'}]),
        F('remise', 'Remise (%)', 'percent', default='0', min=0, max=100),
        F('rabais', 'Rabais (%)', 'percent', default='0', min=0, max=100),
        F('ristourne', 'Ristourne (%)', 'percent', default='0', min=0, max=100),
        F('escompte', 'Escompte (%)', 'percent', default='0', min=0, max=100),
        F('port', 'Port / transport facturé HT', default='0', min=0),
        F('emballages', 'Emballages consignés (hors TVA)', default='0', min=0),
        F('vat', 'Taux de TVA (%)', 'percent', default='18', min=0, max=100, help=TVA_HELP),
    ],
)
def calc_facture(d):
    r = Result()
    rows = []
    gross = ZERO
    for line in d['lines']:
        amount = money(line['quantity'] * line['unit_price'])
        gross += amount
        rows.append([line['designation'] or '—', fmt(line['quantity']), line['unit_price'], amount])
    r.table('Détail des articles', ['Désignation', 'Quantité', 'Prix unitaire', 'Montant HT'], rows, footer=['Montant brut', '', '', gross])
    r.formulas = ['Net commercial = Brut − remise − rabais − ristourne (en cascade)',
                  'Net financier = Net commercial − escompte',
                  'Base TVA = Net financier + port', 'TTC = Base TVA + TVA',
                  'Net à payer = TTC + emballages consignés']
    base = gross
    for key, label in (('remise', 'Remise'), ('rabais', 'Rabais'), ('ristourne', 'Ristourne')):
        if d[key] > 0:
            red = money(base * pct(d[key]))
            r.step(label, f'{fmt(base)} × {fmt(d[key])} %', red)
            base -= red
    nc = base
    esc = money(nc * pct(d['escompte']))
    nf = nc - esc
    base_tva = nf + d['port']
    tva = money(base_tva * pct(d['vat']))
    ttc = base_tva + tva
    nap = ttc + d['emballages']
    r.step('Net commercial', 'Brut après réductions commerciales', nc)
    if esc:
        r.step('Escompte', f'{fmt(nc)} × {fmt(d["escompte"])} %', esc)
    r.step('Net financier', f'{fmt(nc)} − {fmt(esc)}', nf)
    r.step('Base TVA', f'{fmt(nf)} + port {fmt(d["port"])}', base_tva)
    r.step('TVA', f'{fmt(base_tva)} × {fmt(d["vat"])} %', tva)
    r.step('Net à payer', f'{fmt(ttc)} + emballages {fmt(d["emballages"])}', nap)
    for label, value in (('Montant brut', gross), ('Net commercial', nc), ('Escompte', esc), ('Net financier', nf),
                         ('Base imposable', base_tva), ('TVA', tva), ('Total TTC', ttc)):
        r.result(label, value)
    r.result('Net à payer', nap, highlight=True)

    g = 'Chez l\'acheteur (facture d\'achat)'
    r.entry('601', 'Achats de marchandises', debit=nc, group=g)
    r.entry('6015', 'Frais sur achats (transport)', debit=d['port'], group=g)
    r.entry('4452', 'TVA récupérable sur achats', debit=tva, group=g)
    r.entry('4094', 'Fournisseurs, créances pour emballages à rendre', debit=d['emballages'], group=g)
    r.entry('773', 'Escomptes obtenus', credit=esc, group=g)
    r.entry('401', 'Fournisseurs', credit=nap, group=g)
    g = 'Chez le vendeur (facture de vente)'
    r.entry('411', 'Clients', debit=nap, group=g)
    r.entry('673', 'Escomptes accordés', debit=esc, group=g)
    r.entry('701', 'Ventes de marchandises', credit=nc, group=g)
    r.entry('7071', 'Ports, emballages perdus et autres frais facturés', credit=d['port'], group=g)
    r.entry('4431', 'TVA facturée sur ventes', credit=tva, group=g)
    r.entry('4194', 'Clients, dettes pour emballages consignés', credit=d['emballages'], group=g)
    r.interpretation.append('Les réductions commerciales ne sont pas enregistrées ; l\'escompte, réduction financière, l\'est. '
                            'Les emballages consignés ne supportent pas la TVA : ils sont une créance (acheteur) ou une dette (vendeur).')
    r.warnings.append('Le compte de frais sur achats (6015) et le traitement du port sont à confirmer selon le plan SYSCOHADA révisé utilisé en cours.')
    return r


# --------------------------------------------------------------------------------------
# 5. Achats et ventes — coût d'achat des marchandises vendues et marge
# --------------------------------------------------------------------------------------

@calculator(
    'achats-ventes', 'Achats, ventes et marge commerciale', 'BT1', 'Factures et TVA',
    'Coût d\'achat des marchandises vendues, marge commerciale, taux de marge et taux de marque.',
    [
        F('stock_initial', 'Stock initial de marchandises', default='0', min=0),
        F('purchases', 'Achats de marchandises (HT)', required=True, min=0),
        F('purchase_costs', 'Frais accessoires d\'achat', default='0', min=0),
        F('stock_final', 'Stock final de marchandises', default='0', min=0),
        F('sales', 'Ventes de marchandises (HT)', required=True, min=0),
    ],
)
def calc_achats_ventes(d):
    r = Result()
    variation = d['stock_initial'] - d['stock_final']
    camv = d['purchases'] + d['purchase_costs'] + variation
    marge = d['sales'] - camv
    r.formulas = ['Variation de stock = Stock initial − Stock final',
                  'Coût d\'achat des marchandises vendues = Achats + frais + variation de stock',
                  'Marge commerciale = Ventes − Coût d\'achat des marchandises vendues',
                  'Taux de marge = Marge ÷ Coût d\'achat ; Taux de marque = Marge ÷ Prix de vente HT']
    r.step('Variation de stock', f'{fmt(d["stock_initial"])} − {fmt(d["stock_final"])}', variation)
    r.step('Coût d\'achat des marchandises vendues', f'{fmt(d["purchases"])} + {fmt(d["purchase_costs"])} + ({fmt(variation)})', camv)
    r.step('Marge commerciale', f'{fmt(d["sales"])} − {fmt(camv)}', marge)
    r.result('Variation de stock', variation)
    r.result('Coût d\'achat des marchandises vendues', camv)
    r.result('Marge commerciale', marge, highlight=True)
    if camv:
        r.result('Taux de marge', div(marge, camv) * 100, unit='%')
    if d['sales']:
        r.result('Taux de marque', div(marge, d['sales']) * 100, unit='%')
    r.interpretation.append(
        'Une variation de stock positive (stock qui diminue) augmente le coût des marchandises vendues ; '
        'une variation négative (stock qui augmente) le réduit.')
    if marge < 0:
        r.interpretation.append('La marge est négative : les marchandises sont vendues en dessous de leur coût d\'achat.')
    return r


# --------------------------------------------------------------------------------------
# 8. Amortissements
# --------------------------------------------------------------------------------------

ASSET_TYPES = {
    'logiciel': ('213', 'Logiciels et sites internet', '2813', '6812', 'Dotations aux amortissements des immobilisations incorporelles'),
    'batiment': ('231', 'Bâtiments', '2831', '6813', 'Dotations aux amortissements des immobilisations corporelles'),
    'materiel': ('241', 'Matériel et outillage', '2841', '6813', 'Dotations aux amortissements des immobilisations corporelles'),
    'mobilier': ('244', 'Matériel et mobilier de bureau', '2844', '6813', 'Dotations aux amortissements des immobilisations corporelles'),
    'transport': ('245', 'Matériel de transport', '2845', '6813', 'Dotations aux amortissements des immobilisations corporelles'),
}


def days_360(start: date, end: date) -> int:
    """Nombre de jours selon l'année commerciale de 360 jours (mois de 30 jours)."""
    d1 = min(start.day, 30)
    d2 = min(end.day, 30)
    return (end.year - start.year) * 360 + (end.month - start.month) * 30 + (d2 - d1) + 1


@calculator(
    'amortissement', 'Tableau d\'amortissement', 'BT1', 'Immobilisations',
    'Plan d\'amortissement linéaire ou dégressif avec prorata temporis, VNC et écriture de dotation.',
    [
        F('cost', 'Valeur d\'origine (HT)', required=True, min=0),
        F('residual', 'Valeur résiduelle', default='0', min=0),
        F('start_date', 'Date de mise en service', 'date', required=True, default='2025-04-01'),
        F('years', 'Durée d\'utilisation (années)', 'integer', required=True, min=1, max=100, default='5'),
        F('method', 'Mode d\'amortissement', 'select', default='lineaire', options=options(('lineaire', 'Linéaire'), ('degressif', 'Dégressif'))),
        F('coefficient', 'Coefficient dégressif', 'number', default='2', min=1,
          help='Le coefficient fiscal applicable au Mali dépend de la durée d\'utilisation : à vérifier dans le CGI en vigueur.'),
        F('asset_type', 'Nature de l\'immobilisation', 'select', default='materiel',
          options=options(*[(k, v[1]) for k, v in ASSET_TYPES.items()])),
        F('fiscal_year_end_month', 'Mois de clôture de l\'exercice', 'integer', default='12', min=1, max=12),
    ],
    reference='AUDCIF / SYSCOHADA révisé — amortissement selon la durée d\'utilité.',
)
def calc_amortissement(d):
    r = Result()
    start = d['start_date']
    if start is None:
        raise CalculationError('La date de mise en service est obligatoire.', 'start_date')
    base = d['cost'] - d['residual']
    if base <= 0:
        raise CalculationError('La base amortissable doit être positive (valeur d\'origine > valeur résiduelle).', 'cost')
    n = int(d['years'])
    end_month = int(d['fiscal_year_end_month'])
    rows = []
    cumul = ZERO

    def fy_end(year):
        import calendar
        return date(year, end_month, calendar.monthrange(year, end_month)[1])

    first_end = fy_end(start.year) if start <= fy_end(start.year) else fy_end(start.year + 1)

    if d['method'] == 'lineaire':
        taux = Decimal(1) / n
        annuite = base * taux
        r.formulas = ['Base amortissable = Valeur d\'origine − Valeur résiduelle', 'Taux linéaire = 100 % ÷ durée',
                      'Annuité = Base × taux', '1ʳᵉ annuité = Annuité × jours d\'utilisation ÷ 360 (prorata temporis)']
        r.step('Base amortissable', f'{fmt(d["cost"])} − {fmt(d["residual"])}', base)
        r.step('Taux linéaire', f'100 % ÷ {n}', taux * 100, unit='%')
        r.step('Annuité pleine', f'{fmt(base)} × {fmt(taux * 100)} %', money(annuite))
        days_first = days_360(start, first_end)
        first = money(annuite * Decimal(days_first) / 360)
        r.step('Prorata 1ʳᵉ année', f'{fmt(money(annuite))} × {days_first} ÷ 360', first)
        year_end = first_end
        while cumul < base and len(rows) < n + 2:
            dot = first if not rows else money(annuite)
            dot = min(dot, base - cumul)
            cumul += dot
            rows.append([year_end.year, base, dot, cumul, d['cost'] - cumul])
            year_end = fy_end(year_end.year + 1)
    else:
        coef = d['coefficient']
        taux_lin = Decimal(1) / n
        taux_deg = taux_lin * coef
        r.formulas = ['Taux dégressif = Taux linéaire × coefficient', 'Annuité = VNC début × taux dégressif',
                      'On passe au linéaire lorsque le taux linéaire sur la durée restante ≥ taux dégressif',
                      '1ʳᵉ annuité au prorata des mois à compter du 1er jour du mois d\'acquisition']
        r.step('Taux dégressif', f'{fmt(taux_lin * 100)} % × {fmt(coef)}', taux_deg * 100, unit='%')
        months_first = (first_end.year - start.year) * 12 + first_end.month - start.month + 1
        months_first = min(months_first, 12)
        r.step('Prorata 1ʳᵉ année', f'{months_first} mois sur 12', Decimal(months_first), unit='mois')
        vnc = base
        year_end = first_end
        for i in range(n):
            remaining = n - i
            taux_rest = Decimal(1) / remaining
            if taux_rest >= taux_deg:
                dot = vnc * taux_rest
                applied = f'linéaire {fmt(taux_rest * 100)} %'
            else:
                dot = vnc * taux_deg
                applied = f'dégressif {fmt(taux_deg * 100)} %'
            if i == 0 and months_first < 12 and n > 1:
                dot = dot * Decimal(months_first) / 12
            dot = vnc if i == n - 1 else money(min(dot, vnc))
            cumul += dot
            rows.append([year_end.year, vnc, dot, cumul, d['cost'] - cumul, applied])
            vnc -= dot
            year_end = fy_end(year_end.year + 1)
    cols = ['Exercice', 'Base / VNC début', 'Dotation', 'Cumul amortissements', 'VNC fin']
    if d['method'] == 'degressif':
        cols.append('Taux appliqué')
    r.table('Plan d\'amortissement', cols, rows)
    first_dot = D0 = rows[0][2]
    r.result('Base amortissable', base)
    r.result('Dotation du 1er exercice', first_dot, highlight=True)
    r.result('Nombre d\'exercices', str(len(rows)), unit='')
    acc, acc_label, amort, dot_acc, dot_label = ASSET_TYPES[d['asset_type']]
    g = f'Dotation de l\'exercice {rows[0][0]}'
    r.entry(dot_acc, dot_label, debit=D0, group=g)
    r.entry(amort, f'Amortissements — {acc_label}', credit=D0, group=g)
    r.interpretation.append(
        'L\'amortissement constate la consommation des avantages économiques de l\'immobilisation. '
        'La VNC (valeur nette comptable) = valeur d\'origine − cumul des amortissements figure à l\'actif du bilan.')
    if d['method'] == 'degressif':
        r.warnings.append('Le mode dégressif et ses coefficients relèvent de la réglementation fiscale malienne : vérifier le CGI en vigueur.')
    return r


@calculator(
    'cession', 'Cession d\'immobilisation', 'BT1', 'Immobilisations',
    'Sortie d\'une immobilisation : VNC, plus ou moins-value et écritures de cession.',
    [
        F('cost', 'Valeur d\'origine', required=True, min=0),
        F('accumulated', 'Cumul des amortissements à la date de cession', required=True, min=0),
        F('price', 'Prix de cession', required=True, min=0),
        F('asset_type', 'Nature de l\'immobilisation', 'select', default='materiel',
          options=options(*[(k, v[1]) for k, v in ASSET_TYPES.items()])),
    ],
)
def calc_cession(d):
    r = Result()
    if d['accumulated'] > d['cost']:
        raise CalculationError('Le cumul des amortissements ne peut pas dépasser la valeur d\'origine.', 'accumulated')
    vnc = d['cost'] - d['accumulated']
    pv = d['price'] - vnc
    r.formulas = ['VNC = Valeur d\'origine − Cumul des amortissements', 'Résultat de cession = Prix de cession − VNC']
    r.step('VNC', f'{fmt(d["cost"])} − {fmt(d["accumulated"])}', vnc)
    r.step('Résultat de cession', f'{fmt(d["price"])} − {fmt(vnc)}', pv)
    r.result('Valeur nette comptable', vnc)
    r.result('Plus-value' if pv >= 0 else 'Moins-value', abs(pv), highlight=True)
    acc, label, amort, _, _ = ASSET_TYPES[d['asset_type']]
    corp = d['asset_type'] != 'logiciel'
    g = 'Constatation du prix de cession'
    r.entry('485', 'Créances sur cessions d\'immobilisations', debit=d['price'], group=g)
    r.entry('822' if corp else '821', 'Produits des cessions d\'immobilisations ' + ('corporelles' if corp else 'incorporelles'), credit=d['price'], group=g)
    g = 'Sortie de l\'immobilisation'
    r.entry(amort, f'Amortissements — {label}', debit=d['accumulated'], group=g)
    r.entry('812' if corp else '811', 'Valeurs comptables des cessions d\'immobilisations ' + ('corporelles' if corp else 'incorporelles'), debit=vnc, group=g)
    r.entry(acc, label, credit=d['cost'], group=g)
    r.interpretation.append('Les cessions relèvent des activités hors activités ordinaires (HAO) : le résultat de cession '
                            'apparaît dans le résultat HAO (comptes 81 / 82).')
    return r


# --------------------------------------------------------------------------------------
# 9. Dépréciations et provisions
# --------------------------------------------------------------------------------------

@calculator(
    'depreciation-creances', 'Dépréciation des créances clients', 'BT1', 'Provisions',
    'Créances douteuses : base HT, dépréciation nécessaire, dotation ou reprise.',
    [
        F('clients', 'Créances douteuses', 'table', required=True, columns=[
            F('name', 'Client', 'text'),
            F('ttc', 'Créance TTC', 'money', min=0),
            F('rate', 'Perte probable (%)', 'percent', min=0, max=100),
            F('existing', 'Dépréciation existante', 'money', min=0),
        ], default=[{'name': 'Client K', 'ttc': '590000', 'rate': '40', 'existing': '0'}]),
        F('vat', 'Taux de TVA (%)', 'percent', default='18', min=0, max=100, help=TVA_HELP),
    ],
)
def calc_depreciation_creances(d):
    r = Result()
    r.formulas = ['Créance HT = Créance TTC ÷ (1 + taux TVA)', 'Dépréciation nécessaire = Créance HT × % de perte probable',
                  'Ajustement = Dépréciation nécessaire − Dépréciation existante (> 0 : dotation, < 0 : reprise)']
    rows = []
    tot_dot = tot_rep = ZERO
    for c in d['clients']:
        ht = money(div(c['ttc'], 1 + pct(d['vat'])))
        need = money(ht * pct(c['rate']))
        adj = need - c['existing']
        rows.append([c['name'] or '—', c['ttc'], ht, fmt(c['rate']) + ' %', need, c['existing'],
                     adj if adj > 0 else ZERO, -adj if adj < 0 else ZERO])
        if adj > 0:
            tot_dot += adj
        else:
            tot_rep += -adj
    r.table('État des créances douteuses', ['Client', 'TTC', 'HT', '% perte', 'Dépréciation nécessaire', 'Existante', 'Dotation', 'Reprise'], rows)
    r.result('Total des dotations', tot_dot, highlight=True)
    r.result('Total des reprises', tot_rep)
    total_ttc = sum((c['ttc'] for c in d['clients']), ZERO)
    g = 'Reclassement des clients douteux'
    r.entry('416', 'Créances clients litigieuses ou douteuses', debit=total_ttc, group=g)
    r.entry('411', 'Clients', credit=total_ttc, group=g)
    if tot_dot:
        g = 'Dotation de l\'exercice'
        r.entry('659', 'Charges pour dépréciations et provisions à court terme d\'exploitation', debit=tot_dot, group=g)
        r.entry('491', 'Dépréciations des comptes clients', credit=tot_dot, group=g)
    if tot_rep:
        g = 'Reprise de l\'exercice'
        r.entry('491', 'Dépréciations des comptes clients', debit=tot_rep, group=g)
        r.entry('759', 'Reprises de charges pour dépréciations et provisions à court terme d\'exploitation', credit=tot_rep, group=g)
    r.interpretation.append('La dépréciation se calcule sur le montant HT : la TVA collectée sera récupérée si la créance devient irrécouvrable.')
    r.warnings.append('Le reclassement en 416 ne concerne que les créances devenues douteuses dans l\'exercice. '
                      'Les conditions de déductibilité fiscale relèvent du CGI malien (à vérifier).')
    return r


@calculator(
    'creance-irrecouvrable', 'Créance irrécouvrable', 'BT1', 'Provisions',
    'Constatation d\'une perte définitive sur créance et reprise de la dépréciation antérieure.',
    [
        F('ttc', 'Montant TTC de la créance', required=True, min=0),
        F('existing', 'Dépréciation antérieurement constatée', default='0', min=0),
        F('vat', 'Taux de TVA (%)', 'percent', default='18', min=0, max=100, help=TVA_HELP),
    ],
)
def calc_irrecouvrable(d):
    r = Result()
    ht = money(div(d['ttc'], 1 + pct(d['vat'])))
    tva = d['ttc'] - ht
    r.formulas = ['Perte HT = TTC ÷ (1 + taux)', 'TVA à régulariser = TTC − HT']
    r.step('Perte HT', f'{fmt(d["ttc"])} ÷ {fmt(1 + pct(d["vat"]), 2)}', ht)
    r.step('TVA', f'{fmt(d["ttc"])} − {fmt(ht)}', tva)
    r.result('Perte sur créance (HT)', ht, highlight=True)
    r.result('TVA récupérée', tva)
    g = 'Annulation de la créance'
    r.entry('651', 'Pertes sur créances clients', debit=ht, group=g)
    r.entry('4431', 'TVA facturée sur ventes', debit=tva, group=g)
    r.entry('416', 'Créances clients litigieuses ou douteuses', credit=d['ttc'], group=g)
    if d['existing']:
        g = 'Reprise de la dépréciation devenue sans objet'
        r.entry('491', 'Dépréciations des comptes clients', debit=d['existing'], group=g)
        r.entry('759', 'Reprises de charges pour dépréciations et provisions à court terme d\'exploitation', credit=d['existing'], group=g)
    r.warnings.append('La récupération de la TVA sur créances irrécouvrables est soumise à des conditions fiscales maliennes : à vérifier.')
    return r


@calculator(
    'depreciation-stocks', 'Dépréciation des stocks', 'BT1', 'Provisions',
    'Comparaison coût / valeur actuelle des stocks à l\'inventaire.',
    [
        F('items', 'Stocks', 'table', required=True, columns=[
            F('name', 'Article', 'text'),
            F('cost', 'Coût d\'entrée', 'money', min=0),
            F('market', 'Valeur actuelle (nette de réalisation)', 'money', min=0),
            F('existing', 'Dépréciation existante', 'money', min=0),
        ], default=[{'name': 'Marchandises', 'cost': '800000', 'market': '720000', 'existing': '0'}]),
    ],
)
def calc_depreciation_stocks(d):
    r = Result()
    r.formulas = ['Dépréciation nécessaire = max(0 ; Coût − Valeur actuelle)', 'Ajustement = Nécessaire − Existante']
    rows = []
    dot = rep = ZERO
    for it in d['items']:
        need = max(ZERO, it['cost'] - it['market'])
        adj = need - it['existing']
        dot += max(adj, ZERO)
        rep += max(-adj, ZERO)
        rows.append([it['name'] or '—', it['cost'], it['market'], need, it['existing'], max(adj, ZERO), max(-adj, ZERO)])
    r.table('Dépréciation des stocks', ['Article', 'Coût', 'Valeur actuelle', 'Nécessaire', 'Existante', 'Dotation', 'Reprise'], rows)
    r.result('Dotation', dot, highlight=True)
    r.result('Reprise', rep)
    if dot:
        r.entry('659', 'Charges pour dépréciations et provisions à court terme d\'exploitation', debit=dot, group='Dotation')
        r.entry('39', 'Dépréciations des stocks', credit=dot, group='Dotation')
    if rep:
        r.entry('39', 'Dépréciations des stocks', debit=rep, group='Reprise')
        r.entry('759', 'Reprises de charges pour dépréciations et provisions à court terme d\'exploitation', credit=rep, group='Reprise')
    r.interpretation.append('Principe de prudence : les stocks sont évalués au plus bas du coût et de la valeur actuelle.')
    return r


# --------------------------------------------------------------------------------------
# 10. Rapprochement bancaire
# --------------------------------------------------------------------------------------

SENS = options(('in', 'Encaissement (+)'), ('out', 'Décaissement (−)'))


@calculator(
    'rapprochement', 'État de rapprochement bancaire', 'BT1', 'Trésorerie',
    'Rapproche le compte 521 de l\'entreprise et le relevé bancaire, puis génère les écritures de régularisation.',
    [
        F('book_balance', 'Solde du compte 521 chez l\'entreprise (débiteur +)', required=True),
        F('bank_balance', 'Solde du relevé bancaire (créditeur +)', required=True),
        F('bank_only', 'Opérations du relevé non comptabilisées par l\'entreprise', 'table', columns=[
            F('label', 'Libellé', 'text'),
            F('direction', 'Sens', 'select', options=SENS),
            F('amount', 'Montant', 'money', min=0),
            F('account', 'Compte de contrepartie', 'text'),
        ], default=[{'label': 'Frais de tenue de compte', 'direction': 'out', 'amount': '7500', 'account': '631'},
                    {'label': 'Virement client', 'direction': 'in', 'amount': '150000', 'account': '411'}]),
        F('book_only', 'Opérations de l\'entreprise non encore au relevé', 'table', columns=[
            F('label', 'Libellé', 'text'),
            F('direction', 'Sens', 'select', options=SENS),
            F('amount', 'Montant', 'money', min=0),
        ], default=[{'label': 'Chèque émis non encaissé', 'direction': 'out', 'amount': '85000'}]),
    ],
)
def calc_rapprochement(d):
    r = Result()
    r.formulas = ['Solde entreprise rectifié = Solde 521 + encaissements du relevé non comptabilisés − décaissements du relevé non comptabilisés',
                  'Solde banque rectifié = Solde relevé + encaissements de l\'entreprise non relevés − décaissements non relevés',
                  'Les deux soldes rectifiés doivent être égaux.']
    book = d['book_balance']
    bank = d['bank_balance']
    rows = [['Solde de départ', book if book >= 0 else '', -book if book < 0 else '', bank if bank >= 0 else '', -bank if bank < 0 else '']]
    for op in d['bank_only']:
        signed = op['amount'] if op['direction'] == 'in' else -op['amount']
        book += signed
        rows.append([op['label'] or '—', op['amount'] if signed > 0 else '', op['amount'] if signed < 0 else '', '', ''])
    for op in d['book_only']:
        signed = op['amount'] if op['direction'] == 'in' else -op['amount']
        bank += signed
        rows.append([op['label'] or '—', '', '', op['amount'] if signed > 0 else '', op['amount'] if signed < 0 else ''])
    rows.append(['Soldes rectifiés', book, '', bank, ''])
    r.table('État de rapprochement', ['Libellé', 'Entreprise (débit)', 'Entreprise (crédit)', 'Banque (débit)', 'Banque (crédit)'], rows)
    r.result('Solde rectifié entreprise', book)
    r.result('Solde rectifié banque', bank)
    ok = money(book) == money(bank)
    r.result('Rapprochement', 'Équilibré ✔' if ok else f'Écart de {fcfa(money(book - bank))}', unit='', highlight=True)
    for i, op in enumerate(d['bank_only'], start=1):
        acc = op['account'] or ('631' if op['direction'] == 'out' else '411')
        g = f'Régularisation {i} : {op["label"] or "opération bancaire"}'
        if op['direction'] == 'in':
            r.entry('521', 'Banques locales', debit=op['amount'], group=g)
            r.entry(acc, op['label'] or 'Contrepartie', credit=op['amount'], group=g)
        else:
            r.entry(acc, op['label'] or 'Contrepartie', debit=op['amount'], group=g)
            r.entry('521', 'Banques locales', credit=op['amount'], group=g)
    if not ok:
        r.warnings.append('Les soldes rectifiés ne concordent pas : vérifier les montants, les sens et rechercher une erreur ou une omission.')
    r.interpretation.append('Seules les opérations figurant sur le relevé et non comptabilisées donnent lieu à écriture chez l\'entreprise ; '
                            'les opérations de l\'entreprise non encore relevées seront enregistrées par la banque.')
    return r


# --------------------------------------------------------------------------------------
# 11. Bilan
# --------------------------------------------------------------------------------------

@calculator(
    'bilan', 'Bilan simplifié', 'BT1', 'États financiers',
    'Construit le bilan par grandes masses SYSCOHADA, contrôle l\'équilibre et déduit le résultat si besoin.',
    [
        F('immobilisations', 'Actif immobilisé net', default='0', min=0),
        F('stocks', 'Stocks', default='0', min=0),
        F('creances', 'Créances et emplois assimilés', default='0', min=0),
        F('tresorerie_actif', 'Trésorerie – Actif', default='0', min=0),
        F('capital', 'Capital', default='0'),
        F('reserves', 'Réserves et report à nouveau', default='0'),
        F('resultat', 'Résultat net (laisser vide pour le déduire)', nullable=True),
        F('dettes_financieres', 'Dettes financières et ressources assimilées', default='0', min=0),
        F('dettes_circulantes', 'Passif circulant (fournisseurs, fiscales, sociales…)', default='0', min=0),
        F('tresorerie_passif', 'Trésorerie – Passif', default='0', min=0),
    ],
)
def calc_bilan(d):
    r = Result()
    actif_circ = d['stocks'] + d['creances']
    total_actif = d['immobilisations'] + actif_circ + d['tresorerie_actif']
    passif_hors_res = d['capital'] + d['reserves'] + d['dettes_financieres'] + d['dettes_circulantes'] + d['tresorerie_passif']
    derived = d['resultat'] is None
    resultat = total_actif - passif_hors_res if derived else d['resultat']
    cp = d['capital'] + d['reserves'] + resultat
    total_passif = cp + d['dettes_financieres'] + d['dettes_circulantes'] + d['tresorerie_passif']
    r.formulas = ['Total actif = Actif immobilisé + Actif circulant + Trésorerie-actif',
                  'Total passif = Capitaux propres + Dettes financières + Passif circulant + Trésorerie-passif',
                  'Résultat = Total actif − (Passif hors résultat)']
    if derived:
        r.step('Résultat déduit', f'{fmt(total_actif)} − {fmt(passif_hors_res)}', resultat)
    r.table('Bilan', ['Actif', 'Montant', 'Passif', 'Montant'], [
        ['Actif immobilisé', d['immobilisations'], 'Capital', d['capital']],
        ['Stocks', d['stocks'], 'Réserves / report à nouveau', d['reserves']],
        ['Créances', d['creances'], 'Résultat net', resultat],
        ['Trésorerie – Actif', d['tresorerie_actif'], 'Capitaux propres', cp],
        ['', '', 'Dettes financières', d['dettes_financieres']],
        ['', '', 'Passif circulant', d['dettes_circulantes']],
        ['', '', 'Trésorerie – Passif', d['tresorerie_passif']],
    ], footer=['TOTAL ACTIF', total_actif, 'TOTAL PASSIF', total_passif])
    r.result('Total actif', total_actif)
    r.result('Total passif', total_passif)
    r.result('Capitaux propres', cp)
    r.result('Résultat net', resultat, highlight=True)
    if money(total_actif) != money(total_passif):
        r.warnings.append(f'Le bilan n\'est pas équilibré : écart de {fcfa(money(total_actif - total_passif))}.')
    if resultat >= 0:
        r.interpretation.append(f'Bénéfice de {fcfa(resultat)} : il augmente les capitaux propres.')
    else:
        r.interpretation.append(f'Perte de {fcfa(-resultat)} : elle diminue les capitaux propres.')
    return r


# --------------------------------------------------------------------------------------
# 12. Compte de résultat (soldes significatifs SYSCOHADA révisé)
# --------------------------------------------------------------------------------------

@calculator(
    'compte-resultat', 'Compte de résultat et soldes intermédiaires', 'BT1', 'États financiers',
    'Calcule marge commerciale, valeur ajoutée, EBE, résultat d\'exploitation, financier, HAO et résultat net.',
    [
        F('ventes_march', 'Ventes de marchandises', default='0', min=0),
        F('achats_march', 'Achats de marchandises', default='0', min=0),
        F('var_stock_march', 'Variation de stocks de marchandises (SI − SF)', default='0'),
        F('production_vendue', 'Ventes de produits fabriqués, travaux et services', default='0', min=0),
        F('produits_accessoires', 'Produits accessoires', default='0', min=0),
        F('production_stockee', 'Production stockée (ou déstockage)', default='0'),
        F('production_immobilisee', 'Production immobilisée', default='0', min=0),
        F('subventions', 'Subventions d\'exploitation', default='0', min=0),
        F('autres_produits', 'Autres produits', default='0', min=0),
        F('achats_mp', 'Achats de matières et fournitures (+ variation)', default='0'),
        F('autres_achats', 'Autres achats (+ variation)', default='0'),
        F('transports', 'Transports', default='0', min=0),
        F('services_ext', 'Services extérieurs', default='0', min=0),
        F('impots_taxes', 'Impôts et taxes', default='0', min=0),
        F('autres_charges', 'Autres charges', default='0', min=0),
        F('personnel', 'Charges de personnel', default='0', min=0),
        F('reprises_exploit', 'Reprises de provisions et transferts de charges d\'exploitation', default='0', min=0),
        F('dotations_exploit', 'Dotations aux amortissements et provisions d\'exploitation', default='0', min=0),
        F('produits_fin', 'Produits financiers', default='0', min=0),
        F('charges_fin', 'Charges financières', default='0', min=0),
        F('produits_hao', 'Produits HAO', default='0', min=0),
        F('charges_hao', 'Charges HAO', default='0', min=0),
        F('participation', 'Participation des travailleurs', default='0', min=0),
        F('impot', 'Impôt sur le résultat', default='0', min=0),
    ],
    reference='Structure du compte de résultat SYSCOHADA révisé (soldes XA à XI) — libellés à confronter au modèle officiel.',
)
def calc_compte_resultat(d):
    r = Result()
    xa = d['ventes_march'] - d['achats_march'] - d['var_stock_march']
    xb = d['ventes_march'] + d['production_vendue'] + d['produits_accessoires']
    xc = (xb + d['production_stockee'] + d['production_immobilisee'] + d['subventions'] + d['autres_produits']
          - d['achats_march'] - d['var_stock_march'] - d['achats_mp'] - d['autres_achats'] - d['transports']
          - d['services_ext'] - d['impots_taxes'] - d['autres_charges'])
    xd = xc - d['personnel']
    xe = xd + d['reprises_exploit'] - d['dotations_exploit']
    xf = d['produits_fin'] - d['charges_fin']
    xg = xe + xf
    xh = d['produits_hao'] - d['charges_hao']
    xi = xg + xh - d['participation'] - d['impot']
    r.formulas = [
        'XA Marge commerciale = Ventes de marchandises − Achats de marchandises − Variation de stocks',
        'XB Chiffre d\'affaires = Ventes de marchandises + Production vendue + Produits accessoires',
        'XC Valeur ajoutée = CA + production stockée et immobilisée + subventions + autres produits − consommations externes',
        'XD Excédent brut d\'exploitation = Valeur ajoutée − Charges de personnel',
        'XE Résultat d\'exploitation = EBE + reprises et transferts − dotations',
        'XF Résultat financier = Produits financiers − Charges financières',
        'XG Résultat des activités ordinaires = XE + XF', 'XH Résultat HAO = Produits HAO − Charges HAO',
        'XI Résultat net = XG + XH − Participation − Impôt sur le résultat']
    rows = [['XA', 'Marge commerciale', xa], ['XB', 'Chiffre d\'affaires', xb], ['XC', 'Valeur ajoutée', xc],
            ['XD', 'Excédent brut d\'exploitation', xd], ['XE', 'Résultat d\'exploitation', xe],
            ['XF', 'Résultat financier', xf], ['XG', 'Résultat des activités ordinaires', xg],
            ['XH', 'Résultat hors activités ordinaires', xh], ['XI', 'Résultat net', xi]]
    r.table('Soldes significatifs de gestion', ['Réf.', 'Solde', 'Montant'], rows)
    for ref, label, value in rows:
        r.result(f'{ref} — {label}', value, highlight=ref == 'XI')
    r.interpretation.append('L\'EBE mesure la performance économique avant politique d\'amortissement et de financement.')
    r.interpretation.append(('Bénéfice net' if xi >= 0 else 'Perte nette') + f' de {fcfa(abs(xi))}.')
    return r
