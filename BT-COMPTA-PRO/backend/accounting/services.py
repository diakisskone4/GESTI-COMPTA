"""Règles métier du moteur comptable."""
from collections import OrderedDict
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Max, Q, Sum
from django.utils import timezone

from .data.syscohada import CHARGE_8, CLASSES
from .models import Account, EntryLine, FiscalYear, Journal, JournalEntry

ZERO = Decimal('0')

DEFAULT_JOURNALS = [
    ('AC', 'Journal des achats', Journal.Kind.PURCHASES),
    ('VT', 'Journal des ventes', Journal.Kind.SALES),
    ('BQ', 'Journal de banque', Journal.Kind.BANK),
    ('CA', 'Journal de caisse', Journal.Kind.CASH),
    ('OD', 'Journal des opérations diverses', Journal.Kind.MISC),
]


def create_default_journals(company):
    for code, label, kind in DEFAULT_JOURNALS:
        Journal.objects.get_or_create(company=company, code=code, defaults={'label': label, 'kind': kind})


def accounts_for(company):
    return Account.objects.filter(Q(company__isnull=True) | Q(company=company), is_active=True)


def check_entry(entry: JournalEntry):
    """Contrôles exigés avant validation. Lève ValidationError avec un message clair."""
    errors = []
    lines = list(entry.lines.select_related('account'))
    if len(lines) < 2:
        errors.append('Une écriture comporte au moins deux lignes (partie double).')
    debit = sum((l.debit for l in lines), ZERO)
    credit = sum((l.credit for l in lines), ZERO)
    if debit != credit:
        errors.append(f'Écriture déséquilibrée : total débit {debit} ≠ total crédit {credit}.')
    if debit == 0:
        errors.append('Le montant de l\'écriture ne peut pas être nul.')
    for l in lines:
        if l.debit == 0 and l.credit == 0:
            errors.append(f'La ligne du compte {l.account.code} n\'a pas de montant.')
        if l.account.company_id not in (None, entry.company_id):
            errors.append(f'Le compte {l.account.code} n\'appartient pas à cette entreprise.')
    fy = entry.fiscal_year
    if fy.is_closed:
        errors.append('L\'exercice est clôturé : aucune écriture ne peut y être validée.')
    if not (fy.start_date <= entry.date <= fy.end_date):
        errors.append(f'La date {entry.date:%d/%m/%Y} est hors de l\'exercice ({fy.start_date:%d/%m/%Y} – {fy.end_date:%d/%m/%Y}).')
    if errors:
        raise ValidationError({'detail': errors})


@transaction.atomic
def validate_entry(entry: JournalEntry, user):
    entry = JournalEntry.objects.select_for_update().get(pk=entry.pk)
    if entry.is_locked:
        raise ValidationError({'detail': ['Cette écriture est déjà validée.']})
    check_entry(entry)
    last = JournalEntry.objects.filter(fiscal_year=entry.fiscal_year).aggregate(m=Max('number'))['m'] or 0
    entry.number = last + 1
    entry.status = JournalEntry.Status.VALIDATED
    entry.validated_by = user
    entry.validated_at = timezone.now()
    entry.save(update_fields=['number', 'status', 'validated_by', 'validated_at'])
    return entry


@transaction.atomic
def reverse_entry(entry: JournalEntry, user, date=None, reason=''):
    """Contre-passation d'une écriture validée : crée une écriture inverse en brouillard puis la valide."""
    if not entry.is_locked:
        raise ValidationError({'detail': ['Seule une écriture validée peut être contre-passée (un brouillard se modifie directement).']})
    if hasattr(entry, 'reversed_by'):
        raise ValidationError({'detail': ['Cette écriture a déjà été contre-passée.']})
    reversal = JournalEntry.objects.create(
        company=entry.company, fiscal_year=entry.fiscal_year, journal=entry.journal, date=date or entry.date,
        reference=entry.reference, label=f'Contre-passation de l\'écriture n° {entry.number} — {reason or entry.label}'[:255],
        reversal_of=entry, created_by=user)
    EntryLine.objects.bulk_create([
        EntryLine(entry=reversal, account=l.account, label=l.label, debit=l.credit, credit=l.debit)
        for l in entry.lines.all()
    ])
    return validate_entry(reversal, user)


def _lines(company, fiscal_year, include_drafts=False, date_to=None):
    qs = EntryLine.objects.filter(entry__company=company, entry__fiscal_year=fiscal_year)
    if not include_drafts:
        qs = qs.filter(entry__status=JournalEntry.Status.VALIDATED)
    if date_to:
        qs = qs.filter(entry__date__lte=date_to)
    return qs


def trial_balance(company, fiscal_year, include_drafts=False):
    rows = (_lines(company, fiscal_year, include_drafts)
            .values('account__code', 'account__label')
            .annotate(debit=Sum('debit'), credit=Sum('credit'))
            .order_by('account__code'))
    result = []
    totals = {'debit': ZERO, 'credit': ZERO, 'balance_debit': ZERO, 'balance_credit': ZERO}
    for r in rows:
        solde = r['debit'] - r['credit']
        item = {
            'code': r['account__code'], 'label': r['account__label'], 'debit': r['debit'], 'credit': r['credit'],
            'balance_debit': solde if solde > 0 else ZERO, 'balance_credit': -solde if solde < 0 else ZERO,
        }
        for k in totals:
            totals[k] += item[k]
        result.append(item)
    totals['balanced'] = totals['debit'] == totals['credit'] and totals['balance_debit'] == totals['balance_credit']
    return {'rows': result, 'totals': totals}


def general_ledger(company, fiscal_year, account_code=None, include_drafts=False):
    qs = (_lines(company, fiscal_year, include_drafts)
          .select_related('account', 'entry', 'entry__journal')
          .order_by('account__code', 'entry__date', 'entry__number', 'id'))
    if account_code:
        qs = qs.filter(account__code__startswith=account_code)
    accounts = OrderedDict()
    for l in qs:
        acc = accounts.setdefault(l.account.code, {'code': l.account.code, 'label': l.account.label, 'lines': [],
                                                    'debit': ZERO, 'credit': ZERO, 'balance': ZERO})
        acc['debit'] += l.debit
        acc['credit'] += l.credit
        acc['balance'] += l.debit - l.credit
        acc['lines'].append({
            'date': l.entry.date, 'journal': l.entry.journal.code, 'number': l.entry.number, 'reference': l.entry.reference,
            'label': l.label or l.entry.label, 'debit': l.debit, 'credit': l.credit, 'balance': acc['balance'],
            'status': l.entry.status,
        })
    return list(accounts.values())


def _balances(company, fiscal_year):
    return {r['code']: r['balance_debit'] - r['balance_credit'] for r in trial_balance(company, fiscal_year)['rows']}


def income_statement(company, fiscal_year):
    balances = _balances(company, fiscal_year)
    charges, produits = OrderedDict(), OrderedDict()
    for code, solde in balances.items():
        c = code[0]
        group = code[:2]
        if c == '6' or (c == '8' and group in CHARGE_8):
            charges[group] = charges.get(group, ZERO) + solde
        elif c == '7' or c == '8':
            produits[group] = produits.get(group, ZERO) - solde
    from .data.syscohada import label_for
    total_c = sum(charges.values(), ZERO)
    total_p = sum(produits.values(), ZERO)
    return {
        'charges': [{'code': k, 'label': label_for(k), 'amount': v} for k, v in sorted(charges.items())],
        'produits': [{'code': k, 'label': label_for(k), 'amount': v} for k, v in sorted(produits.items())],
        'total_charges': total_c, 'total_produits': total_p, 'result': total_p - total_c,
    }


def balance_sheet(company, fiscal_year):
    """Bilan par grandes masses SYSCOHADA à partir des soldes (actif net des amortissements et dépréciations)."""
    balances = _balances(company, fiscal_year)
    result = income_statement(company, fiscal_year)['result']
    actif = OrderedDict((k, ZERO) for k in ('Actif immobilisé', 'Actif circulant', 'Trésorerie – Actif'))
    passif = OrderedDict((k, ZERO) for k in ('Capitaux propres', 'Dettes financières', 'Passif circulant', 'Trésorerie – Passif'))
    detail = []
    for code, solde in balances.items():
        c, g = code[0], code[:2]
        if c == '1':
            key = 'Capitaux propres' if g in ('10', '11', '12', '13', '14', '15') else 'Dettes financières'
            passif[key] -= solde
        elif c == '2':
            actif['Actif immobilisé'] += solde  # 28/29 créditeurs viennent en diminution
        elif c == '3':
            actif['Actif circulant'] += solde
        elif c == '4':
            if g == '49':
                actif['Actif circulant'] += solde
            elif solde > 0:
                actif['Actif circulant'] += solde
            else:
                passif['Passif circulant'] -= solde
        elif c == '5':
            if solde < 0:
                passif['Trésorerie – Passif'] -= solde
            else:
                actif['Trésorerie – Actif'] += solde
        else:
            continue
        detail.append({'code': code, 'balance': solde})
    passif['Capitaux propres'] += result
    total_a = sum(actif.values(), ZERO)
    total_p = sum(passif.values(), ZERO)
    return {
        'actif': [{'label': k, 'amount': v} for k, v in actif.items()],
        'passif': [{'label': k, 'amount': v} for k, v in passif.items()],
        'result': result, 'total_actif': total_a, 'total_passif': total_p, 'balanced': total_a == total_p,
        'note': 'Présentation par grandes masses ; le résultat de l\'exercice est inclus dans les capitaux propres.',
    }


def class_label(code):
    return CLASSES.get(code[:1], '')
