from datetime import date as date_cls
from decimal import Decimal

from django.db.models import Q
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import mixins, permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError as DRFValidationError
from rest_framework.response import Response

from core.audit import log_action
from core.params import int_param
from core.permissions import ReadOnlyOrTeacher, has_role
from reports.exports import build_pdf, build_xlsx

from . import services
from .models import Account, AccountingRule, Company, FiscalYear, Journal, JournalEntry, TaxRate
from .serializers import (AccountingRuleSerializer, AccountSerializer, CompanySerializer, FiscalYearSerializer,
                          JournalEntrySerializer, JournalSerializer, TaxRateSerializer)


def user_companies(user):
    return Company.objects.all() if user.is_superuser else Company.objects.filter(owner=user)


class AccountViewSet(viewsets.ModelViewSet):
    """Plan de comptes : plan officiel (lecture) + sous-comptes propres à chaque entreprise."""

    serializer_class = AccountSerializer

    def get_queryset(self):
        qs = Account.objects.all()
        company_id = int_param(self.request, 'company')
        if company_id:
            company = get_object_or_404(user_companies(self.request.user), pk=company_id)
            qs = qs.filter(Q(company__isnull=True) | Q(company=company))
        else:
            qs = qs.filter(company__isnull=True) if self.action == 'list' else qs.filter(
                Q(company__isnull=True) | Q(company__in=user_companies(self.request.user)))
        account_class = self.request.query_params.get('class')
        search = self.request.query_params.get('search')
        if account_class:
            qs = qs.filter(account_class=account_class)
        if search:
            qs = qs.filter(Q(code__startswith=search) | Q(label__icontains=search))
        return qs.order_by('code')

    def _ensure_custom(self, instance):
        if instance.company_id is None and not has_role(self.request.user, 'admin'):
            raise DRFValidationError('Les comptes du plan officiel ne sont modifiables que par un administrateur.')
        if instance.lines.exists() and self.action == 'destroy':
            raise DRFValidationError('Ce compte est utilisé dans des écritures : désactivez-le plutôt que de le supprimer.')

    def perform_update(self, serializer):
        self._ensure_custom(serializer.instance)
        serializer.save()

    def perform_destroy(self, instance):
        self._ensure_custom(instance)
        instance.delete()


class TaxRateViewSet(viewsets.ModelViewSet):
    queryset = TaxRate.objects.all()
    serializer_class = TaxRateSerializer
    permission_classes = [ReadOnlyOrTeacher]


class AccountingRuleViewSet(viewsets.ModelViewSet):
    queryset = AccountingRule.objects.filter(is_active=True)
    serializer_class = AccountingRuleSerializer
    permission_classes = [ReadOnlyOrTeacher]


class CompanyViewSet(viewsets.ModelViewSet):
    serializer_class = CompanySerializer

    def get_queryset(self):
        return user_companies(self.request.user)

    def perform_create(self, serializer):
        company = serializer.save()
        log_action(self.request, 'company.created', company, name=company.name)

    def perform_destroy(self, instance):
        if instance.entries.filter(status=JournalEntry.Status.VALIDATED).exists():
            raise DRFValidationError('Impossible de supprimer une entreprise ayant des écritures validées.')
        log_action(self.request, 'company.deleted', instance, name=instance.name)
        instance.delete()

    def _fiscal_year(self, company):
        fy_id = int_param(self.request, 'fiscal_year')
        qs = company.fiscal_years.all()
        if fy_id:
            return get_object_or_404(qs, pk=fy_id)
        fy = qs.first()
        if fy is None:
            raise DRFValidationError('Créez d\'abord un exercice comptable.')
        return fy

    @action(detail=True, methods=['get'], url_path='trial-balance')
    def trial_balance(self, request, pk=None):
        company = self.get_object()
        fy = self._fiscal_year(company)
        data = services.trial_balance(company, fy, include_drafts=request.query_params.get('drafts') == '1')
        return self._maybe_export(request, f'Balance générale — {company.name} — {fy.label}', data, 'trial_balance')

    @action(detail=True, methods=['get'], url_path='ledger')
    def ledger(self, request, pk=None):
        company = self.get_object()
        fy = self._fiscal_year(company)
        data = services.general_ledger(company, fy, request.query_params.get('account'),
                                       include_drafts=request.query_params.get('drafts') == '1')
        return self._maybe_export(request, f'Grand livre — {company.name} — {fy.label}', data, 'ledger')

    @action(detail=True, methods=['get'], url_path='income-statement')
    def income_statement(self, request, pk=None):
        company = self.get_object()
        fy = self._fiscal_year(company)
        return self._maybe_export(request, f'Compte de résultat — {company.name} — {fy.label}',
                                  services.income_statement(company, fy), 'income')

    @action(detail=True, methods=['get'], url_path='balance-sheet')
    def balance_sheet(self, request, pk=None):
        company = self.get_object()
        fy = self._fiscal_year(company)
        return self._maybe_export(request, f'Bilan — {company.name} — {fy.label}', services.balance_sheet(company, fy), 'bilan')

    @action(detail=True, methods=['get'], url_path='journal')
    def journal_export(self, request, pk=None):
        company = self.get_object()
        fy = self._fiscal_year(company)
        entries = company.entries.filter(fiscal_year=fy).prefetch_related('lines__account').select_related('journal')
        rows = []
        for e in entries:
            for l in e.lines.all():
                rows.append([f'{e.date:%d/%m/%Y}', e.journal.code, e.number or 'Brouillard', e.reference, l.account.code,
                             l.label or e.label, _n(l.debit), _n(l.credit)])
        doc = {'title': f'Journal — {company.name} — {fy.label}', 'subtitle': 'Toutes écritures',
               'sections': [{'title': 'Écritures', 'columns': ['Date', 'Journal', 'N°', 'Pièce', 'Compte', 'Libellé', 'Débit', 'Crédit'],
                             'rows': rows}]}
        return _file(doc, request.query_params.get('export', 'pdf'), 'journal')

    def _maybe_export(self, request, title, data, kind):
        fmt = request.query_params.get('export')
        if not fmt:
            return Response(as_json(data))
        return _file(_document(title, data, kind), fmt, kind)


def as_json(data):
    """Convertit récursivement les Decimal en chaînes exactes (jamais de float pour un montant)."""
    if isinstance(data, Decimal):
        return f'{data:.2f}'
    if isinstance(data, dict):
        return {k: as_json(v) for k, v in data.items()}
    if isinstance(data, (list, tuple)):
        return [as_json(v) for v in data]
    return data


def _n(value):
    return f'{value:,.2f}'.replace(',', ' ').replace('.', ',') if value else ''


def _document(title, data, kind):
    sections = []
    if kind == 'trial_balance':
        sections.append({'title': 'Balance', 'columns': ['Compte', 'Intitulé', 'Débit', 'Crédit', 'Solde débiteur', 'Solde créditeur'],
                         'rows': [[r['code'], r['label'], _n(r['debit']), _n(r['credit']), _n(r['balance_debit']), _n(r['balance_credit'])] for r in data['rows']],
                         'footer': ['', 'TOTAUX', _n(data['totals']['debit']), _n(data['totals']['credit']),
                                    _n(data['totals']['balance_debit']), _n(data['totals']['balance_credit'])]})
    elif kind == 'ledger':
        for acc in data:
            sections.append({'title': f'{acc["code"]} — {acc["label"]}', 'columns': ['Date', 'Journal', 'N°', 'Libellé', 'Débit', 'Crédit', 'Solde'],
                             'rows': [[f'{l["date"]:%d/%m/%Y}', l['journal'], l['number'] or '', l['label'], _n(l['debit']), _n(l['credit']), _n(l['balance'])] for l in acc['lines']],
                             'footer': ['', '', '', 'Totaux', _n(acc['debit']), _n(acc['credit']), _n(acc['balance'])]})
    elif kind == 'income':
        sections.append({'title': 'Charges', 'columns': ['Compte', 'Intitulé', 'Montant'],
                         'rows': [[c['code'], c['label'], _n(c['amount'])] for c in data['charges']],
                         'footer': ['', 'Total charges', _n(data['total_charges'])]})
        sections.append({'title': 'Produits', 'columns': ['Compte', 'Intitulé', 'Montant'],
                         'rows': [[c['code'], c['label'], _n(c['amount'])] for c in data['produits']],
                         'footer': ['', 'Total produits', _n(data['total_produits'])]})
        sections.append({'title': 'Résultat', 'lines': [f'Résultat net : {_n(data["result"]) or "0"} FCFA']})
    elif kind == 'bilan':
        sections.append({'title': 'Actif', 'columns': ['Poste', 'Montant'], 'rows': [[a['label'], _n(a['amount'])] for a in data['actif']],
                         'footer': ['Total actif', _n(data['total_actif'])]})
        sections.append({'title': 'Passif', 'columns': ['Poste', 'Montant'], 'rows': [[a['label'], _n(a['amount'])] for a in data['passif']],
                         'footer': ['Total passif', _n(data['total_passif'])]})
    return {'title': title, 'subtitle': f'Édité le {timezone.localdate():%d/%m/%Y} — écritures validées', 'sections': sections}


def _file(doc, fmt, name):
    if fmt == 'xlsx':
        response = HttpResponse(build_xlsx(doc), content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        response['Content-Disposition'] = f'attachment; filename="{name}.xlsx"'
    else:
        response = HttpResponse(build_pdf(doc), content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="{name}.pdf"'
    return response


class FiscalYearViewSet(viewsets.ModelViewSet):
    serializer_class = FiscalYearSerializer

    def get_queryset(self):
        qs = FiscalYear.objects.filter(company__in=user_companies(self.request.user))
        company = int_param(self.request, 'company')
        return qs.filter(company_id=company) if company else qs

    def perform_destroy(self, instance):
        if instance.entries.exists():
            raise DRFValidationError('Impossible de supprimer un exercice contenant des écritures.')
        instance.delete()

    @action(detail=True, methods=['post'])
    def close(self, request, pk=None):
        fy = self.get_object()
        if fy.is_closed:
            raise DRFValidationError('Exercice déjà clôturé.')
        if fy.entries.filter(status=JournalEntry.Status.DRAFT).exists():
            raise DRFValidationError('Des écritures sont encore en brouillard : validez-les ou supprimez-les avant la clôture.')
        tb = services.trial_balance(fy.company, fy)
        if not tb['totals']['balanced']:
            raise DRFValidationError('La balance n\'est pas équilibrée.')
        fy.is_closed = True
        fy.closed_at = timezone.now()
        fy.save(update_fields=['is_closed', 'closed_at'])
        log_action(request, 'fiscal_year.closed', fy)
        return Response(FiscalYearSerializer(fy, context={'request': request}).data)


class JournalViewSet(viewsets.ModelViewSet):
    serializer_class = JournalSerializer

    def get_queryset(self):
        qs = Journal.objects.filter(company__in=user_companies(self.request.user))
        company = int_param(self.request, 'company')
        return qs.filter(company_id=company) if company else qs

    def perform_destroy(self, instance):
        if instance.entries.exists():
            raise DRFValidationError('Ce journal contient des écritures.')
        instance.delete()


class JournalEntryViewSet(viewsets.ModelViewSet):
    serializer_class = JournalEntrySerializer

    def get_queryset(self):
        qs = (JournalEntry.objects.filter(company__in=user_companies(self.request.user))
              .select_related('journal', 'reversed_by').prefetch_related('lines__account'))
        p = self.request.query_params
        for field, param in (('company_id', 'company'), ('fiscal_year_id', 'fiscal_year'), ('journal_id', 'journal')):
            value = int_param(self.request, param)
            if value is not None:
                qs = qs.filter(**{field: value})
        if p.get('status') in ('draft', 'validated'):
            qs = qs.filter(status=p['status'])
        return qs.order_by('-date', '-id')

    def perform_create(self, serializer):
        entry = serializer.save()
        log_action(self.request, 'entry.created', entry)

    def perform_update(self, serializer):
        if serializer.instance.is_locked:
            raise DRFValidationError('Écriture validée : modification interdite. Utilisez la contre-passation.')
        entry = serializer.save()
        log_action(self.request, 'entry.updated', entry)

    def perform_destroy(self, instance):
        if instance.is_locked:
            raise DRFValidationError('Écriture validée : suppression interdite. Utilisez la contre-passation.')
        log_action(self.request, 'entry.deleted_draft', instance, label=instance.label)
        instance.delete()

    @action(detail=True, methods=['post'])
    def validate(self, request, pk=None):
        entry = services.validate_entry(self.get_object(), request.user)
        log_action(request, 'entry.validated', entry, number=entry.number)
        return Response(self.get_serializer(entry).data)

    @action(detail=True, methods=['post'])
    def reverse(self, request, pk=None):
        entry = self.get_object()
        raw_date = request.data.get('date')
        try:
            on = date_cls.fromisoformat(raw_date) if raw_date else None
        except ValueError:
            raise DRFValidationError({'date': 'Date invalide.'})
        reversal = services.reverse_entry(entry, request.user, on, request.data.get('reason', ''))
        log_action(request, 'entry.reversed', entry, reversal_id=reversal.id, reason=request.data.get('reason', ''))
        return Response(self.get_serializer(reversal).data, status=status.HTTP_201_CREATED)
