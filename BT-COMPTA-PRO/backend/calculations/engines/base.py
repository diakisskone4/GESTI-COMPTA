"""Socle du moteur de calcul de BT COMPTA PRO.

* Toutes les valeurs monétaires sont des ``Decimal`` (jamais de float).
* Chaque calculatrice déclare ses champs de saisie : le frontend construit le formulaire
  automatiquement à partir de cette description.
* Chaque calcul renvoie : formule(s), données utilisées, étapes détaillées, résultats,
  tableaux éventuels, écritures comptables et interprétation pédagogique.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from decimal import ROUND_HALF_UP, Decimal, DivisionByZero, InvalidOperation
from typing import Any, Callable

MAX_TABLE_ROWS = 300       # surchargé par settings.CALC_MAX_TABLE_ROWS
MAX_TEXT_LENGTH = 200
MAX_AMOUNT = Decimal('1e15')  # 1 million de milliards de FCFA

TWO = Decimal('0.01')
FOUR = Decimal('0.0001')
ZERO = Decimal('0')
HUNDRED = Decimal('100')


class CalculationError(ValueError):
    """Erreur de saisie : le message est affiché tel quel à l'utilisateur."""

    def __init__(self, message: str, field_name: str | None = None):
        super().__init__(message)
        self.field_name = field_name


def D(value: Any, field_name: str | None = None) -> Decimal:
    """Convertit une saisie (str, int, Decimal) en Decimal. Accepte la virgule décimale et les espaces."""
    if value is None or value == '':
        return ZERO
    if isinstance(value, Decimal):
        return value
    if isinstance(value, bool):
        raise CalculationError('Valeur numérique attendue.', field_name)
    if isinstance(value, int):
        return Decimal(value)
    if isinstance(value, float):
        return Decimal(str(value))
    text = str(value).strip().replace(' ', '').replace('\xa0', '').replace(' ', '').replace(',', '.')
    try:
        result = Decimal(text)
    except InvalidOperation:
        raise CalculationError(f'« {value} » n\'est pas un nombre valide.', field_name)
    if not result.is_finite():
        raise CalculationError('Nombre invalide.', field_name)
    return result


def money(value: Decimal) -> Decimal:
    return value.quantize(TWO, rounding=ROUND_HALF_UP)


def rate(value: Decimal) -> Decimal:
    return value.quantize(FOUR, rounding=ROUND_HALF_UP)


def div(a: Decimal, b: Decimal, what: str = 'diviseur') -> Decimal:
    if b == 0:
        raise CalculationError(f'Division par zéro : le {what} ne peut pas être nul.')
    try:
        return a / b
    except (DivisionByZero, InvalidOperation):
        raise CalculationError(f'Division impossible ({what}).')


def pct(value: Decimal) -> Decimal:
    """Convertit un pourcentage saisi (18) en taux (0.18)."""
    return value / HUNDRED


def fmt(value: Decimal, decimals: int = 2) -> str:
    """Format français : 1 234 567,89."""
    q = Decimal(1).scaleb(-decimals) if decimals else Decimal(1)
    value = value.quantize(q, rounding=ROUND_HALF_UP)
    sign = '-' if value < 0 else ''
    integer, _, frac = f'{abs(value):f}'.partition('.')
    groups = []
    while len(integer) > 3:
        groups.insert(0, integer[-3:])
        integer = integer[:-3]
    groups.insert(0, integer)
    text = ' '.join(groups)
    if decimals and frac and int(frac) != 0:
        text += ',' + frac
    return sign + text


def fcfa(value: Decimal) -> str:
    return f'{fmt(value)} FCFA'


def fpct(value: Decimal) -> str:
    """Affiche un taux (0.18) en pourcentage (18 %)."""
    return f'{fmt(value * HUNDRED, 2)} %'


def parse_date(value: Any, field_name: str | None = None) -> date | None:
    if not value:
        return None
    if isinstance(value, date):
        return value
    try:
        return date.fromisoformat(str(value)[:10])
    except ValueError:
        raise CalculationError(f'Date invalide : « {value} » (format attendu AAAA-MM-JJ).', field_name)


# --------------------------------------------------------------------------------------
# Résultat d'un calcul
# --------------------------------------------------------------------------------------

@dataclass
class Result:
    formulas: list[str] = field(default_factory=list)
    steps: list[dict] = field(default_factory=list)
    results: list[dict] = field(default_factory=list)
    tables: list[dict] = field(default_factory=list)
    entries: list[dict] = field(default_factory=list)
    interpretation: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    def step(self, label: str, detail: str, value: Decimal | str | None = None, unit: str = 'FCFA'):
        if isinstance(value, Decimal):
            value = f'{fmt(value)} {unit}'.strip() if unit else fmt(value)
        self.steps.append({'label': label, 'detail': detail, 'value': value or ''})

    def result(self, label: str, value: Decimal | str, unit: str = 'FCFA', highlight: bool = False, key: str | None = None):
        raw = None
        if isinstance(value, Decimal):
            raw = str(money(value)) if unit == 'FCFA' else str(rate(value))
            display = f'{fmt(value)} {unit}'.strip()
        else:
            display = value
        self.results.append({'key': key or label, 'label': label, 'value': display, 'raw': raw, 'highlight': highlight})

    def table(self, title: str, columns: list[str], rows: list[list[Any]], footer: list[Any] | None = None):
        def cell(v):
            if isinstance(v, Decimal):
                return fmt(v)
            return '' if v is None else str(v)
        self.tables.append({
            'title': title,
            'columns': columns,
            'rows': [[cell(v) for v in row] for row in rows],
            'footer': [cell(v) for v in footer] if footer else None,
        })

    def entry(self, account: str, label: str, debit: Decimal = ZERO, credit: Decimal = ZERO, group: str = ''):
        if debit == 0 and credit == 0:
            return
        self.entries.append({
            'group': group,
            'account': account,
            'label': label,
            'debit': str(money(debit)) if debit else '',
            'credit': str(money(credit)) if credit else '',
        })

    def check_entries_balanced(self):
        groups: dict[str, list[Decimal]] = {}
        for e in self.entries:
            g = groups.setdefault(e['group'], [ZERO, ZERO])
            g[0] += D(e['debit'])
            g[1] += D(e['credit'])
        for name, (debit, credit) in groups.items():
            if money(debit) != money(credit):
                raise AssertionError(f'Écriture déséquilibrée ({name}) : {debit} ≠ {credit}')

    def as_dict(self) -> dict:
        self.check_entries_balanced()
        return {
            'formulas': self.formulas,
            'steps': self.steps,
            'results': self.results,
            'tables': self.tables,
            'entries': self.entries,
            'interpretation': self.interpretation,
            'warnings': self.warnings,
        }


# --------------------------------------------------------------------------------------
# Registre des calculatrices
# --------------------------------------------------------------------------------------

@dataclass
class Calculator:
    slug: str
    title: str
    level: str          # 'BT1' ou 'BT2'
    category: str
    description: str
    fields: list[dict]
    func: Callable[[dict], Result]
    reference: str = ''

    def meta(self) -> dict:
        return {
            'slug': self.slug, 'title': self.title, 'level': self.level, 'category': self.category,
            'description': self.description, 'fields': self.fields, 'reference': self.reference,
        }

    def run(self, data: dict) -> dict:
        clean = self.clean(data or {})
        return self.func(clean).as_dict()

    def clean(self, data: dict) -> dict:
        if not isinstance(data, dict):
            raise CalculationError('Format de données invalide.')
        """Valide et convertit les saisies selon la déclaration des champs."""
        clean: dict[str, Any] = {}
        for f in self.fields:
            clean[f['name']] = self._clean_value(f, data.get(f['name'], f.get('default')))
        return clean

    def _clean_value(self, f: dict, value: Any):
        name, ftype, label = f['name'], f.get('type', 'money'), f['label']
        required = f.get('required', False)
        if ftype == 'table':
            rows = value or []
            if not isinstance(rows, list):
                raise CalculationError(f'{label} : liste de lignes attendue.', name)
            if len(rows) > MAX_TABLE_ROWS:
                raise CalculationError(f'{label} : {MAX_TABLE_ROWS} lignes au maximum.', name)
            cleaned = []
            for i, row in enumerate(rows, start=1):
                if not isinstance(row, dict):
                    raise CalculationError(f'{label}, ligne {i} : format invalide.', name)
                if all(row.get(c['name']) in (None, '') for c in f['columns']):
                    continue  # ligne vide ignorée
                cleaned.append({c['name']: self._clean_value({**c, 'label': f'{label}, ligne {i}, {c["label"]}', 'name': name}, row.get(c['name']))
                                for c in f['columns']})
            if required and not cleaned:
                raise CalculationError(f'{label} : au moins une ligne est requise.', name)
            return cleaned
        if value in (None, ''):
            if required:
                raise CalculationError(f'{label} est obligatoire.', name)
            if f.get('nullable'):
                return None
            if ftype in ('money', 'number', 'percent', 'integer'):
                return ZERO
            return value if value is not None else ''
        if ftype in ('money', 'number', 'percent', 'integer'):
            if len(str(value)) > 40:
                raise CalculationError(f'{label} : nombre trop long.', name)
            number = D(value, name)
            if abs(number) >= MAX_AMOUNT:
                raise CalculationError(f'{label} : montant hors limites.', name)
            if f.get('min') is not None and number < D(f['min']):
                raise CalculationError(f'{label} doit être supérieur ou égal à {f["min"]}.', name)
            if f.get('max') is not None and number > D(f['max']):
                raise CalculationError(f'{label} doit être inférieur ou égal à {f["max"]}.', name)
            if ftype == 'integer' and number != number.to_integral_value():
                raise CalculationError(f'{label} doit être un nombre entier.', name)
            return number
        if ftype == 'select':
            allowed = [o['value'] for o in f.get('options', [])]
            if value not in allowed:
                raise CalculationError(f'{label} : choix invalide.', name)
            return value
        if ftype == 'date':
            return parse_date(value, name)
        text = str(value).strip()
        if len(text) > MAX_TEXT_LENGTH:
            raise CalculationError(f'{label} : {MAX_TEXT_LENGTH} caractères au maximum.', name)
        return text


REGISTRY: dict[str, Calculator] = {}


def calculator(slug: str, title: str, level: str, category: str, description: str, fields: list[dict], reference: str = ''):
    def decorator(func: Callable[[dict], Result]):
        if slug in REGISTRY:
            raise RuntimeError(f'Calculatrice en double : {slug}')
        REGISTRY[slug] = Calculator(slug, title, level, category, description, fields, func, reference)
        return func
    return decorator


# Raccourcis de déclaration de champs ------------------------------------------------------

def F(name, label, type='money', default=None, required=False, help='', **extra):
    spec = {'name': name, 'label': label, 'type': type, 'required': required}
    if default is not None:
        spec['default'] = default
    if help:
        spec['help'] = help
    spec.update(extra)
    return spec


def options(*pairs):
    return [{'value': v, 'label': l} for v, l in pairs]


TVA_HELP = ('Taux standard de TVA retenu par défaut : 18 %. Source : Code général des impôts du Mali — '
            'à vérifier avec la loi de finances en vigueur avant usage professionnel.')
