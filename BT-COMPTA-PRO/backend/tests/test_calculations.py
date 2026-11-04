"""Tests des formules : chaque valeur attendue a été recalculée à la main (détail en commentaire)."""
from decimal import Decimal

from django.test import SimpleTestCase

from calculations.engines import REGISTRY, CalculationError


def run(slug, **data):
    return REGISTRY[slug].run(data)


def res(output, label_start):
    for r in output['results']:
        if r['label'].startswith(label_start):
            return Decimal(r['raw']) if r['raw'] is not None else r['value']
    raise AssertionError(f'Résultat « {label_start} » absent : {[r["label"] for r in output["results"]]}')


def entries(output, group=None):
    return {(e['account'], 'D' if e['debit'] else 'C'): Decimal(e['debit'] or e['credit'])
            for e in output['entries'] if group is None or e['group'].startswith(group)}


class AllCalculatorsTests(SimpleTestCase):
    def test_every_calculator_runs_with_examples_and_entries_balance(self):
        self.assertGreaterEqual(len(REGISTRY), 36)
        for slug, calc in REGISTRY.items():
            with self.subTest(slug=slug):
                out = calc.run({})  # as_dict() vérifie l'équilibre de chaque groupe d'écritures
                self.assertTrue(out['results'], slug)
                self.assertTrue(out['formulas'], slug)

    def test_invalid_number_is_reported(self):
        with self.assertRaises(CalculationError):
            run('tva', amount='abc')
        with self.assertRaises(CalculationError):
            run('tva', amount='-5')


class BT1Tests(SimpleTestCase):
    def test_tva_from_ht_and_ttc(self):
        out = run('tva', mode='ht', amount='100000', rate='18')
        self.assertEqual(res(out, 'TVA'), Decimal('18000.00'))
        self.assertEqual(res(out, 'Montant TTC'), Decimal('118000.00'))
        out = run('tva', mode='ttc', amount='1 180 000', rate='18')
        self.assertEqual(res(out, 'Montant HT'), Decimal('1000000.00'))

    def test_reductions_cascade(self):
        # 800 000 × 0,90 = 720 000 ; × 0,95 = 684 000
        out = run('reductions', gross='800000', remise='10', rabais='5')
        self.assertEqual(res(out, 'Net commercial'), Decimal('684000.00'))
        self.assertEqual(res(out, 'Total des réductions'), Decimal('116000.00'))

    def test_escompte_and_entries(self):
        # escompte 10 000 ; NF 490 000 ; TVA 88 200 ; NAP 578 200
        out = run('escompte', net_commercial='500000', rate='2', vat='18')
        self.assertEqual(res(out, 'Net à payer'), Decimal('578200.00'))
        e = entries(out, 'Chez l\'acheteur')
        self.assertEqual(e[('601', 'D')], Decimal('500000.00'))
        self.assertEqual(e[('773', 'C')], Decimal('10000.00'))
        self.assertEqual(e[('401', 'C')], Decimal('578200.00'))

    def test_facture_complete(self):
        # brut 1 000 000 ; remise 10 % → 900 000 ; escompte 2 % = 18 000 → NF 882 000 ;
        # base TVA 882 000 + port 20 000 = 902 000 ; TVA 162 360 ; TTC 1 064 360 ; + emballages 30 000 = 1 094 360
        out = run('facture', lines=[{'designation': 'A', 'quantity': '100', 'unit_price': '10000'}],
                  remise='10', escompte='2', port='20000', emballages='30000', vat='18')
        self.assertEqual(res(out, 'Net commercial'), Decimal('900000.00'))
        self.assertEqual(res(out, 'TVA'), Decimal('162360.00'))
        self.assertEqual(res(out, 'Net à payer'), Decimal('1094360.00'))
        e = entries(out, 'Chez le vendeur')
        self.assertEqual(e[('411', 'D')], Decimal('1094360.00'))
        self.assertEqual(e[('4194', 'C')], Decimal('30000.00'))

    def test_achats_ventes(self):
        # CAMV = 2 000 000 + 0 + (400 000 − 550 000) = 1 850 000 ; marge = 2 900 000 − 1 850 000 = 1 050 000
        out = run('achats-ventes', stock_initial='400000', purchases='2000000', purchase_costs='0', stock_final='550000', sales='2900000')
        self.assertEqual(res(out, 'Coût d\'achat des marchandises vendues'), Decimal('1850000.00'))
        self.assertEqual(res(out, 'Marge commerciale'), Decimal('1050000.00'))

    def test_amortissement_lineaire_prorata(self):
        # 6 000 000 / 5 ans = 1 200 000 ; 1re année 9 mois = 900 000 ; 6e exercice = 300 000
        out = run('amortissement', cost='6000000', start_date='2025-04-01', years='5', method='lineaire')
        rows = out['tables'][0]['rows']
        self.assertEqual(len(rows), 6)
        self.assertEqual(rows[0][2], '900 000')
        self.assertEqual(rows[1][2], '1 200 000')
        self.assertEqual(rows[-1][2], '300 000')
        self.assertEqual(rows[-1][4], '0')
        e = entries(out)
        self.assertEqual(e[('6813', 'D')], Decimal('900000.00'))
        self.assertEqual(e[('2841', 'C')], Decimal('900000.00'))

    def test_amortissement_degressif(self):
        # taux 40 % : 400 000 ; 240 000 ; 144 000 ; bascule linéaire sur 2 ans : 108 000 ; 108 000
        out = run('amortissement', cost='1000000', start_date='2025-01-01', years='5', method='degressif', coefficient='2')
        dots = [r[2] for r in out['tables'][0]['rows']]
        self.assertEqual(dots, ['400 000', '240 000', '144 000', '108 000', '108 000'])

    def test_cession(self):
        out = run('cession', cost='6000000', accumulated='2100000', price='4500000')
        self.assertEqual(res(out, 'Valeur nette comptable'), Decimal('3900000.00'))
        self.assertEqual(res(out, 'Plus-value'), Decimal('600000.00'))

    def test_depreciation_creances(self):
        # 1 180 000 TTC → 1 000 000 HT × 40 % = 400 000 ; existante 150 000 → dotation 250 000
        out = run('depreciation-creances', clients=[{'name': 'K', 'ttc': '1180000', 'rate': '40', 'existing': '150000'}], vat='18')
        self.assertEqual(res(out, 'Total des dotations'), Decimal('250000.00'))
        e = entries(out, 'Dotation')
        self.assertEqual(e[('659', 'D')], Decimal('250000.00'))
        self.assertEqual(e[('491', 'C')], Decimal('250000.00'))

    def test_rapprochement_equilibre(self):
        # entreprise : 1 250 000 + 150 000 − 7 500 = 1 392 500 ; banque : 1 477 500 − 85 000 = 1 392 500
        out = run('rapprochement', book_balance='1250000', bank_balance='1477500')
        self.assertEqual(res(out, 'Solde rectifié entreprise'), Decimal('1392500.00'))
        self.assertEqual(res(out, 'Solde rectifié banque'), Decimal('1392500.00'))
        self.assertEqual(out['warnings'], [])
        e = entries(out, 'Régularisation 1')
        self.assertEqual(e[('631', 'D')], Decimal('7500.00'))

    def test_bilan_deduit_resultat(self):
        out = run('bilan', immobilisations='5000000', stocks='1000000', creances='800000', tresorerie_actif='700000',
                  capital='5000000', dettes_circulantes='1500000')
        self.assertEqual(res(out, 'Résultat net'), Decimal('1000000.00'))
        self.assertEqual(res(out, 'Total actif'), res(out, 'Total passif'))

    def test_compte_resultat(self):
        # XA = 10 000 000 − 6 000 000 + 200 000 = 4 200 000 ; VA = 4 200 000 − 900 000 = 3 300 000 ;
        # EBE = 1 800 000 ; RE = 1 200 000 ; RAO = 1 050 000 ; RN = 750 000
        out = run('compte-resultat', ventes_march='10000000', achats_march='6000000', var_stock_march='-200000',
                  services_ext='900000', personnel='1500000', dotations_exploit='600000', charges_fin='150000', impot='300000')
        self.assertEqual(res(out, 'XA'), Decimal('4200000.00'))
        self.assertEqual(res(out, 'XC'), Decimal('3300000.00'))
        self.assertEqual(res(out, 'XD'), Decimal('1800000.00'))
        self.assertEqual(res(out, 'XI'), Decimal('750000.00'))


class StocksTests(SimpleTestCase):
    MOVES = [
        {'date': '05/01', 'label': 'Achat', 'kind': 'in', 'quantity': '200', 'unit_cost': '1100'},
        {'date': '10/01', 'label': 'Vente', 'kind': 'out', 'quantity': '250', 'unit_cost': ''},
        {'date': '18/01', 'label': 'Achat', 'kind': 'in', 'quantity': '300', 'unit_cost': '1200'},
        {'date': '25/01', 'label': 'Vente', 'kind': 'out', 'quantity': '180', 'unit_cost': ''},
    ]

    def test_fifo(self):
        # sorties : 100×1000 + 150×1100 = 265 000 ; 50×1100 + 130×1200 = 211 000 → 476 000 ; stock 170×1200 = 204 000
        out = run('fifo', initial_qty='100', initial_cost='1000', movements=self.MOVES)
        self.assertEqual(res(out, 'Coût des sorties'), Decimal('476000.00'))
        self.assertEqual(res(out, 'Stock final (valeur)'), Decimal('204000.00'))

    def test_cump_periode(self):
        # CUMP = (100 000 + 220 000 + 360 000) / 600 = 1 133,33… ; stock 170 × CUMP = 192 666,67
        out = run('cump', mode='periode', initial_qty='100', initial_cost='1000', movements=self.MOVES)
        self.assertEqual(res(out, 'CUMP final'), Decimal('1133.33'))
        self.assertEqual(res(out, 'Stock final (valeur)'), Decimal('192666.67'))

    def test_cump_mobile(self):
        # CUMP1 = 320 000 / 300 = 1 066,67 ; sortie 250 → 266 666,67 ; reste 50 pour 53 333,33
        # CUMP2 = 413 333,33 / 350 = 1 180,95 ; sortie 180 → 212 571,43 ; stock 170 → 200 761,90
        out = run('cump', mode='mobile', initial_qty='100', initial_cost='1000', movements=self.MOVES)
        self.assertEqual(res(out, 'Stock final (valeur)'), Decimal('200761.90'))
        self.assertEqual(res(out, 'Coût des sorties'), Decimal('479238.10'))

    def test_exit_above_stock_is_rejected(self):
        with self.assertRaises(CalculationError):
            run('fifo', initial_qty='10', initial_cost='100', movements=[{'kind': 'out', 'quantity': '11', 'date': '1', 'label': 'x'}])


class LedgerTests(SimpleTestCase):
    def test_unbalanced_entry_detected(self):
        out = run('journal', lines=[
            {'piece': 'P1', 'account': '601', 'debit': '1000', 'credit': ''},
            {'piece': 'P1', 'account': '401', 'debit': '', 'credit': '900'},
        ])
        self.assertTrue(out['warnings'])

    def test_balance_totals(self):
        out = run('balance')
        self.assertEqual(res(out, 'Total mouvements débit'), res(out, 'Total mouvements crédit'))
        self.assertEqual(res(out, 'Total soldes débiteurs'), res(out, 'Total soldes créditeurs'))

    def test_line_with_both_sides_rejected(self):
        with self.assertRaises(CalculationError):
            run('journal', lines=[{'account': '601', 'debit': '10', 'credit': '10'}])


class AnalyticalTests(SimpleTestCase):
    def test_incorporables(self):
        out = run('charges-incorporables', charges_cg='10000000', non_incorporables='300000', remuneration_exploitant='500000')
        self.assertEqual(res(out, 'Charges incorporables'), Decimal('10200000.00'))

    def test_repartition_prestations_reciproques(self):
        # A = 600 000 + 0,1 E ; E = 400 000 + 0,1 A → A = 646 464,65 ; E = 464 646,46
        # Atelier = 1 500 000 + 0,5 A + 0,6 E = 2 102 020,20 → / 2 000 h = 1 051,01
        out = run('repartition')
        self.assertEqual(res(out, 'Coût de l\'UO — Atelier'), Decimal('1051.01'))
        self.assertEqual(res(out, 'Total des charges indirectes'), Decimal('3300000.00'))
        self.assertEqual(out['warnings'], [])

    def test_seuil_et_point_mort(self):
        # MCV 8 000 000 ; taux 40 % ; SR = 6 000 000 / 0,4 = 15 000 000 ; point mort 9 mois
        out = run('seuil-rentabilite', revenue='20000000', variable_costs='12000000', fixed_costs='6000000')
        self.assertEqual(res(out, 'Seuil de rentabilité'), Decimal('15000000.00'))
        self.assertEqual(res(out, 'Levier opérationnel'), Decimal('4.0000'))
        out = run('point-mort', revenue='20000000', variable_costs='12000000', fixed_costs='6000000')
        self.assertEqual(res(out, 'Point mort'), Decimal('9.0000'))
        self.assertIn('30 septembre', res(out, 'Date du point mort'))

    def test_ecarts(self):
        # matières : E/Q = (7 800 − 7 600) × 500 = 100 000 ; E/P = (490 − 500) × 7 800 = −78 000
        # centre : Cs = 1 000 ; BF = 1 980 000 ; budget 50 000 ; activité 30 000 ; rendement 50 000 ; global 130 000
        out = run('ecarts')
        rows = {(r[0], r[1]): r[2] for r in out['tables'][0]['rows']}
        self.assertEqual(rows[('Matières', 'Quantité')], '100 000')
        self.assertEqual(rows[('Matières', 'Prix')], '-78 000')
        self.assertEqual(rows[('Charges indirectes', 'Budget')], '50 000')
        self.assertEqual(rows[('Charges indirectes', 'Activité')], '30 000')
        self.assertEqual(rows[('Charges indirectes', 'Rendement')], '50 000')
        self.assertEqual(res(out, 'Écart global charges indirectes'), Decimal('130000.00'))

    def test_cout_revient(self):
        out = run('cout-revient', quantity_sold='3500', unit_production_cost='1800', distribution_cost='1350000', unit_price='2600')
        # 6 300 000 + 1 350 000 = 7 650 000 ; CA 9 100 000 ; résultat 1 450 000
        self.assertEqual(res(out, 'Coût de revient'), Decimal('7650000.00'))
        self.assertEqual(res(out, 'Résultat analytique'), Decimal('1450000.00'))


class BudgetFinanceTests(SimpleTestCase):
    def test_budget_production(self):
        # 1 200 + 400 − 300 = 1 300 ; 1 350 + 450 − 400 = 1 400 ; 1 500 + 350 − 450 = 1 400 → 4 100
        out = run('budget-production')
        self.assertEqual(res(out, 'Production totale'), Decimal('4100.0000'))

    def test_budget_tresorerie(self):
        out = run('budget-tresorerie', initial_cash='300000', periods=[{'period': 'M1', 'receipts': '2000000', 'payments': '2450000'}])
        self.assertEqual(res(out, 'Trésorerie finale'), Decimal('-150000.00'))

    def test_equilibre_financier(self):
        data = dict(capitaux_propres='12000000', dettes_financieres='5000000', actif_immobilise='14000000', stocks='2000000',
                    creances='3000000', passif_circulant='3500000', tresorerie_actif='2000000', tresorerie_passif='500000')
        self.assertEqual(res(run('frng', **data), 'Fonds de roulement'), Decimal('3000000.00'))
        self.assertEqual(res(run('bfr', **data), 'Besoin de financement'), Decimal('1500000.00'))
        out = run('tresorerie-nette', **data)
        self.assertEqual(res(out, 'Trésorerie nette'), Decimal('1500000.00'))
        self.assertEqual(out['warnings'], [])

    def test_ratios(self):
        out = run('ratios', capitaux_propres='18000000', dettes_financieres='7000000', actif_immobilise='20000000',
                  stocks='4500000', creances='6000000', passif_circulant='5800000', tresorerie_actif='1300000', tresorerie_passif='1000000')
        # AC = 11 800 000 ; DCT = 6 800 000 → 1,7353
        self.assertEqual(res(out, 'Liquidité générale'), Decimal('1.7353'))
