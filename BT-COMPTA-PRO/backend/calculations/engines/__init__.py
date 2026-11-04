"""Moteur de calcul : importer les modules enregistre toutes les calculatrices dans REGISTRY."""
from . import analytical, budgets, bt1, financial, ledger, stocks  # noqa: F401
from .base import REGISTRY, CalculationError  # noqa: F401

# Valeurs d'exemple pré-remplies dans les formulaires (exercices pédagogiques cohérents).
EXAMPLES = {
    'tva': {'amount': '250000'},
    'reductions': {'gross': '1000000', 'remise': '10', 'rabais': '5'},
    'escompte': {'net_commercial': '500000', 'rate': '2'},
    'achats-ventes': {'stock_initial': '400000', 'purchases': '2000000', 'purchase_costs': '50000', 'stock_final': '550000', 'sales': '2900000'},
    'amortissement': {'cost': '6000000'},
    'cession': {'cost': '6000000', 'accumulated': '2100000', 'price': '4500000'},
    'creance-irrecouvrable': {'ttc': '590000', 'existing': '200000'},
    'rapprochement': {'book_balance': '1250000', 'bank_balance': '1477500'},
    'bilan': {'immobilisations': '5000000', 'stocks': '1000000', 'creances': '800000', 'tresorerie_actif': '700000',
              'capital': '5000000', 'dettes_circulantes': '1500000'},
    'compte-resultat': {'ventes_march': '10000000', 'achats_march': '6000000', 'var_stock_march': '-200000',
                        'services_ext': '900000', 'personnel': '1500000', 'dotations_exploit': '600000',
                        'charges_fin': '150000', 'impot': '300000'},
    'charges-incorporables': {'charges_cg': '10000000', 'non_incorporables': '300000', 'remuneration_exploitant': '500000',
                              'directes': '6000000'},
    'cout-unite-oeuvre': {'total': '1500000', 'count': '2500', 'consumed': '300'},
}

for _slug, _values in EXAMPLES.items():
    for _field in REGISTRY[_slug].fields:
        if _field['name'] in _values and 'default' not in _field:
            _field['default'] = _values[_field['name']]

try:  # limite configurable par variable d'environnement
    from django.conf import settings as _settings
    from . import base as _base
    _base.MAX_TABLE_ROWS = getattr(_settings, 'CALC_MAX_TABLE_ROWS', _base.MAX_TABLE_ROWS)
except Exception:  # pragma: no cover - utilisation hors Django
    pass
