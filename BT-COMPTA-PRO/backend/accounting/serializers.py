from decimal import Decimal

from django.db import transaction
from rest_framework import serializers

from .models import Account, AccountingRule, Company, EntryLine, FiscalYear, Journal, JournalEntry, PlanVersion, TaxRate
from .services import accounts_for, create_default_journals


class OwnedCompanyMixin:
    """Restreint le champ ``company`` aux entreprises de l'utilisateur connecté."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        request = self.context.get('request')
        if request and 'company' in self.fields and not self.fields['company'].read_only:
            qs = Company.objects.all() if request.user.is_superuser else Company.objects.filter(owner=request.user)
            self.fields['company'].queryset = qs


class PlanVersionSerializer(serializers.ModelSerializer):
    class Meta:
        model = PlanVersion
        fields = '__all__'


class AccountSerializer(OwnedCompanyMixin, serializers.ModelSerializer):
    is_custom = serializers.SerializerMethodField()

    class Meta:
        model = Account
        fields = ('id', 'code', 'label', 'account_class', 'is_active', 'verified', 'company', 'is_custom')
        read_only_fields = ('account_class', 'verified')

    def get_is_custom(self, obj):
        return obj.company_id is not None

    def validate_code(self, value):
        value = value.strip()
        if not value.isdigit() or value[0] == '0':
            raise serializers.ValidationError('Le numéro de compte doit être numérique et commencer par une classe de 1 à 9.')
        return value

    def validate(self, attrs):
        company = attrs.get('company')
        request = self.context['request']
        if company is None:
            raise serializers.ValidationError({'company': 'Un compte personnalisé est rattaché à une entreprise.'})
        if company.owner_id != request.user.id and not request.user.is_superuser:
            raise serializers.ValidationError({'company': 'Entreprise inaccessible.'})
        if Account.objects.filter(company=company, code=attrs['code']).exclude(pk=getattr(self.instance, 'pk', None)).exists():
            raise serializers.ValidationError({'code': 'Ce compte existe déjà pour cette entreprise.'})
        return attrs


class TaxRateSerializer(serializers.ModelSerializer):
    class Meta:
        model = TaxRate
        fields = '__all__'


class AccountingRuleSerializer(serializers.ModelSerializer):
    rule_type_label = serializers.CharField(source='get_rule_type_display', read_only=True)

    class Meta:
        model = AccountingRule
        fields = '__all__'


class CompanySerializer(serializers.ModelSerializer):
    fiscal_years_count = serializers.IntegerField(source='fiscal_years.count', read_only=True)
    entries_count = serializers.IntegerField(source='entries.count', read_only=True)

    class Meta:
        model = Company
        fields = ('id', 'name', 'legal_form', 'tax_id', 'rccm', 'address', 'city', 'currency', 'is_training',
                  'created_at', 'fiscal_years_count', 'entries_count')
        read_only_fields = ('currency', 'created_at')

    @transaction.atomic
    def create(self, validated_data):
        company = Company.objects.create(owner=self.context['request'].user, **validated_data)
        create_default_journals(company)
        return company


class FiscalYearSerializer(OwnedCompanyMixin, serializers.ModelSerializer):
    class Meta:
        model = FiscalYear
        fields = ('id', 'company', 'label', 'start_date', 'end_date', 'is_closed', 'closed_at')
        read_only_fields = ('is_closed', 'closed_at')

    def validate(self, attrs):
        if self.instance and self.instance.is_closed:
            raise serializers.ValidationError('Exercice clôturé : modification interdite.')
        candidate = FiscalYear(pk=getattr(self.instance, 'pk', None))
        for field in ('company', 'label', 'start_date', 'end_date'):
            value = attrs.get(field, getattr(self.instance, field, None) if self.instance else None)
            setattr(candidate, field, value)
        candidate.clean()
        return attrs


class JournalSerializer(OwnedCompanyMixin, serializers.ModelSerializer):
    class Meta:
        model = Journal
        fields = ('id', 'company', 'code', 'label', 'kind')


class EntryLineSerializer(serializers.ModelSerializer):
    account_code = serializers.CharField(source='account.code', read_only=True)
    account_label = serializers.CharField(source='account.label', read_only=True)

    class Meta:
        model = EntryLine
        fields = ('id', 'account', 'account_code', 'account_label', 'label', 'debit', 'credit')

    def validate(self, attrs):
        debit = attrs.get('debit') or Decimal('0')
        credit = attrs.get('credit') or Decimal('0')
        if debit < 0 or credit < 0:
            raise serializers.ValidationError('Les montants doivent être positifs.')
        if debit and credit:
            raise serializers.ValidationError('Une ligne est soit au débit, soit au crédit.')
        if not debit and not credit:
            raise serializers.ValidationError('Chaque ligne doit avoir un montant au débit ou au crédit.')
        return attrs


class JournalEntrySerializer(OwnedCompanyMixin, serializers.ModelSerializer):
    lines = EntryLineSerializer(many=True)
    journal_code = serializers.CharField(source='journal.code', read_only=True)
    status_label = serializers.CharField(source='get_status_display', read_only=True)
    total_debit = serializers.SerializerMethodField()
    total_credit = serializers.SerializerMethodField()
    reversed_by_id = serializers.SerializerMethodField()

    class Meta:
        model = JournalEntry
        fields = ('id', 'company', 'fiscal_year', 'journal', 'journal_code', 'number', 'date', 'reference', 'label',
                  'status', 'status_label', 'reversal_of', 'reversed_by_id', 'validated_at', 'created_at', 'lines',
                  'total_debit', 'total_credit')
        read_only_fields = ('number', 'status', 'reversal_of', 'validated_at', 'created_at')

    def get_total_debit(self, obj):
        return str(sum((l.debit for l in obj.lines.all()), Decimal('0')))

    def get_total_credit(self, obj):
        return str(sum((l.credit for l in obj.lines.all()), Decimal('0')))

    def get_reversed_by_id(self, obj):
        rev = getattr(obj, 'reversed_by', None)
        return rev.id if rev else None

    def validate(self, attrs):
        if self.instance and self.instance.is_locked:
            raise serializers.ValidationError('Écriture validée : modification interdite. Utilisez la contre-passation.')
        company = attrs.get('company') or self.instance.company
        user = self.context['request'].user
        if company.owner_id != user.id and not user.is_superuser:
            raise serializers.ValidationError({'company': 'Entreprise inaccessible.'})
        fy = attrs.get('fiscal_year') or self.instance.fiscal_year
        journal = attrs.get('journal') or self.instance.journal
        if fy.company_id != company.id or journal.company_id != company.id:
            raise serializers.ValidationError('L\'exercice et le journal doivent appartenir à l\'entreprise.')
        if fy.is_closed:
            raise serializers.ValidationError({'fiscal_year': 'Exercice clôturé.'})
        date = attrs.get('date') or self.instance.date
        if not (fy.start_date <= date <= fy.end_date):
            raise serializers.ValidationError({'date': 'La date doit être comprise dans l\'exercice.'})
        lines = attrs.get('lines')
        if lines is not None:
            if len(lines) < 2:
                raise serializers.ValidationError({'lines': 'Au moins deux lignes sont nécessaires.'})
            allowed = set(accounts_for(company).values_list('id', flat=True))
            for l in lines:
                if l['account'].id not in allowed:
                    raise serializers.ValidationError({'lines': f'Compte {l["account"].code} non autorisé pour cette entreprise.'})
        return attrs

    @transaction.atomic
    def create(self, validated_data):
        lines = validated_data.pop('lines')
        entry = JournalEntry.objects.create(created_by=self.context['request'].user, **validated_data)
        EntryLine.objects.bulk_create([EntryLine(entry=entry, **l) for l in lines])
        return entry

    @transaction.atomic
    def update(self, instance, validated_data):
        lines = validated_data.pop('lines', None)
        for k, v in validated_data.items():
            setattr(instance, k, v)
        instance.save()
        if lines is not None:
            instance.lines.all().delete()
            EntryLine.objects.bulk_create([EntryLine(entry=instance, **l) for l in lines])
        return instance
