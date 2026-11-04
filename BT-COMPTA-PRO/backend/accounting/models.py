"""Moteur de comptabilité générale : entreprises, exercices, journaux, plan de comptes, écritures.

Règle fondamentale : une écriture validée n'est jamais modifiée ni supprimée. Toute correction
passe par une contre-passation (écriture inverse) tracée dans le journal d'audit.
"""
from decimal import Decimal

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models


class PlanVersion(models.Model):
    """Version d'un référentiel (plan de comptes, règles fiscales)."""

    code = models.CharField(max_length=60, unique=True)
    label = models.CharField(max_length=200)
    source = models.TextField(blank=True)
    effective_from = models.DateField(null=True, blank=True)
    is_current = models.BooleanField(default=True)
    verified = models.BooleanField(default=False, help_text='Coché une fois confronté au texte officiel.')

    def __str__(self):
        return self.code


class Account(models.Model):
    """Compte du plan. ``company`` vide = compte du plan officiel partagé ; sinon sous-compte propre à une entreprise."""

    version = models.ForeignKey(PlanVersion, on_delete=models.PROTECT, related_name='accounts', null=True, blank=True)
    company = models.ForeignKey('Company', on_delete=models.CASCADE, related_name='custom_accounts', null=True, blank=True)
    code = models.CharField(max_length=12, db_index=True)
    label = models.CharField(max_length=255)
    account_class = models.CharField(max_length=1, editable=False)
    is_active = models.BooleanField(default=True)
    verified = models.BooleanField(default=False)

    class Meta:
        ordering = ['code']
        constraints = [models.UniqueConstraint(fields=['company', 'code'], name='unique_account_per_company',
                                               nulls_distinct=False)]

    def clean(self):
        if not self.code.isdigit():
            raise ValidationError({'code': 'Le numéro de compte doit être composé uniquement de chiffres.'})
        if self.code[0] not in '123456789':
            raise ValidationError({'code': 'La classe du compte doit être comprise entre 1 et 9.'})

    def save(self, *args, **kwargs):
        self.account_class = self.code[:1]
        super().save(*args, **kwargs)

    def __str__(self):
        return f'{self.code} {self.label}'


class TaxRate(models.Model):
    """Taux fiscaux versionnés (dispositions fiscales maliennes, distinctes des règles OHADA)."""

    code = models.CharField(max_length=40)
    label = models.CharField(max_length=200)
    rate = models.DecimalField(max_digits=7, decimal_places=4)
    valid_from = models.DateField(null=True, blank=True)
    valid_to = models.DateField(null=True, blank=True)
    source = models.TextField(blank=True)
    verified = models.BooleanField(default=False)

    class Meta:
        ordering = ['code', '-valid_from']

    def __str__(self):
        return f'{self.label} ({self.rate} %)'


class AccountingRule(models.Model):
    class RuleType(models.TextChoices):
        OHADA = 'ohada', 'Règle comptable OHADA'
        TAX = 'tax', 'Disposition fiscale malienne'

    rule_type = models.CharField(max_length=10, choices=RuleType.choices)
    code = models.CharField(max_length=50)
    label = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    source = models.TextField(blank=True)
    version = models.CharField(max_length=30, default='v1')
    verified = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['rule_type', 'code']

    def __str__(self):
        return f'{self.get_rule_type_display()} {self.code} : {self.label}'


class Company(models.Model):
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='companies')
    name = models.CharField('raison sociale', max_length=200)
    legal_form = models.CharField('forme juridique', max_length=60, blank=True)
    tax_id = models.CharField('NIF', max_length=40, blank=True)
    rccm = models.CharField('RCCM', max_length=60, blank=True)
    address = models.CharField('adresse', max_length=255, blank=True)
    city = models.CharField('ville', max_length=100, blank=True, default='Bamako')
    currency = models.CharField(max_length=10, default='FCFA', editable=False)
    is_training = models.BooleanField('dossier d\'entraînement', default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']
        verbose_name = 'entreprise'

    def __str__(self):
        return self.name


class FiscalYear(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='fiscal_years')
    label = models.CharField(max_length=60)
    start_date = models.DateField()
    end_date = models.DateField()
    is_closed = models.BooleanField(default=False)
    closed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-start_date']
        verbose_name = 'exercice comptable'

    def clean(self):
        if self.start_date and self.end_date and self.start_date >= self.end_date:
            raise ValidationError({'end_date': 'La date de clôture doit être postérieure à la date d\'ouverture.'})
        if self.start_date and self.end_date and self.company_id:
            overlap = FiscalYear.objects.filter(company_id=self.company_id, start_date__lte=self.end_date,
                                                end_date__gte=self.start_date).exclude(pk=self.pk)
            if overlap.exists():
                raise ValidationError('Cet exercice chevauche un exercice existant.')

    def __str__(self):
        return f'{self.company} — {self.label}'


class Journal(models.Model):
    class Kind(models.TextChoices):
        PURCHASES = 'purchases', 'Achats'
        SALES = 'sales', 'Ventes'
        BANK = 'bank', 'Banque'
        CASH = 'cash', 'Caisse'
        MISC = 'misc', 'Opérations diverses'

    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='journals')
    code = models.CharField(max_length=10)
    label = models.CharField(max_length=100)
    kind = models.CharField(max_length=20, choices=Kind.choices, default=Kind.MISC)

    class Meta:
        ordering = ['code']
        constraints = [models.UniqueConstraint(fields=['company', 'code'], name='unique_journal_code')]

    def __str__(self):
        return f'{self.code} — {self.label}'


class JournalEntry(models.Model):
    class Status(models.TextChoices):
        DRAFT = 'draft', 'Brouillard'
        VALIDATED = 'validated', 'Validée'

    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='entries')
    fiscal_year = models.ForeignKey(FiscalYear, on_delete=models.PROTECT, related_name='entries')
    journal = models.ForeignKey(Journal, on_delete=models.PROTECT, related_name='entries')
    number = models.PositiveIntegerField(null=True, blank=True, help_text='Numéro attribué à la validation (séquence sans trou).')
    date = models.DateField()
    reference = models.CharField('pièce justificative', max_length=60, blank=True)
    label = models.CharField('libellé', max_length=255)
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.DRAFT)
    reversal_of = models.OneToOneField('self', null=True, blank=True, on_delete=models.PROTECT, related_name='reversed_by')
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='+')
    created_at = models.DateTimeField(auto_now_add=True)
    validated_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, null=True, blank=True, related_name='+')
    validated_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['date', 'number', 'id']
        verbose_name = 'écriture'
        constraints = [models.UniqueConstraint(fields=['fiscal_year', 'number'], name='unique_entry_number')]

    @property
    def is_locked(self):
        return self.status == self.Status.VALIDATED

    def totals(self):
        debit = sum((l.debit for l in self.lines.all()), Decimal('0'))
        credit = sum((l.credit for l in self.lines.all()), Decimal('0'))
        return debit, credit

    def __str__(self):
        return f'{self.journal.code} {self.number or "brouillard"} {self.date} {self.label}'


class EntryLine(models.Model):
    entry = models.ForeignKey(JournalEntry, on_delete=models.CASCADE, related_name='lines')
    account = models.ForeignKey(Account, on_delete=models.PROTECT, related_name='lines')
    label = models.CharField(max_length=255, blank=True)
    debit = models.DecimalField(max_digits=18, decimal_places=2, default=Decimal('0'))
    credit = models.DecimalField(max_digits=18, decimal_places=2, default=Decimal('0'))

    class Meta:
        ordering = ['id']
        constraints = [
            models.CheckConstraint(condition=models.Q(debit__gte=0) & models.Q(credit__gte=0), name='line_amounts_positive'),
            models.CheckConstraint(condition=~(models.Q(debit__gt=0) & models.Q(credit__gt=0)), name='line_single_side'),
        ]

    def __str__(self):
        return f'{self.account.code} D{self.debit} C{self.credit}'
