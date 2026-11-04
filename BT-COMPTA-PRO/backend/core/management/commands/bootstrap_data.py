"""Charge les données de référence de BT COMPTA PRO (idempotent).

    python manage.py bootstrap_data            # référentiels + catalogue + quiz
    python manage.py bootstrap_data --demo     # + comptes et dossier de démonstration (développement)
"""
from datetime import date
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction

from accounting.data.syscohada import ACCOUNTS, PLAN_VERSION
from accounting.models import Account, AccountingRule, Company, EntryLine, FiscalYear, Journal, JournalEntry, PlanVersion, TaxRate
from accounting.services import create_default_journals, validate_entry
from examinations.data.bank import QUIZZES
from examinations.models import Choice, Question, Quiz
from pedagogy.data.catalog import CATALOG
from pedagogy.models import Chapter, Lesson, Module, ProgrammeLevel

User = get_user_model()

TAX_RATES = [
    ('TVA_STANDARD', 'TVA — taux normal', Decimal('18'), 'Code général des impôts du Mali — taux à confirmer avec la loi de finances en vigueur.'),
]

RULES = [
    ('ohada', 'PRUDENCE', 'Principe de prudence', 'Appréciation raisonnable des faits afin d\'éviter de transférer sur l\'avenir des incertitudes présentes.', 'AUDCIF — à vérifier (article précis)'),
    ('ohada', 'PERMANENCE', 'Permanence des méthodes', 'Les méthodes d\'évaluation et de présentation ne changent pas d\'un exercice à l\'autre sauf exception justifiée.', 'AUDCIF — à vérifier'),
    ('ohada', 'COUT_HISTORIQUE', 'Coût historique', 'Les biens sont enregistrés à leur coût d\'acquisition ou de production.', 'AUDCIF — à vérifier'),
    ('ohada', 'PARTIE_DOUBLE', 'Partie double', 'Toute écriture comporte au moins un débit et un crédit d\'égal montant.', 'SYSCOHADA révisé — fonctionnement des comptes'),
    ('ohada', 'INTANGIBILITE', 'Intangibilité du bilan d\'ouverture', 'Le bilan d\'ouverture d\'un exercice correspond au bilan de clôture de l\'exercice précédent.', 'AUDCIF — à vérifier'),
    ('tax', 'TVA_TAUX', 'Taux de TVA', 'Taux normal de TVA appliqué par défaut dans les calculatrices : 18 %. D\'autres taux ou exonérations peuvent exister.', 'CGI Mali — à vérifier'),
    ('tax', 'AMORT_DEGRESSIF', 'Amortissement dégressif', 'Conditions d\'application et coefficients fixés par la législation fiscale malienne.', 'CGI Mali — à vérifier'),
    ('tax', 'CREANCES_IRRECOUVRABLES', 'Récupération de TVA sur créances irrécouvrables', 'Conditions de récupération de la TVA collectée sur créances définitivement irrécouvrables.', 'CGI Mali — à vérifier'),
]


class Command(BaseCommand):
    help = 'Charge le plan SYSCOHADA, les taux, le catalogue BT1/BT2 et la banque de quiz.'

    def add_arguments(self, parser):
        parser.add_argument('--demo', action='store_true', help='Crée des comptes et un dossier de démonstration.')

    @transaction.atomic
    def handle(self, *args, **options):
        self.load_plan()
        self.load_tax()
        self.load_catalog()
        self.load_quizzes()
        if options['demo']:
            self.load_demo()
        self.stdout.write(self.style.SUCCESS('Données de référence chargées.'))

    def load_plan(self):
        version, _ = PlanVersion.objects.get_or_create(code=PLAN_VERSION, defaults={
            'label': 'Plan comptable SYSCOHADA révisé (extrait de travail)',
            'source': 'Acte uniforme relatif au droit comptable et à l\'information financière (AUDCIF) — libellés à vérifier sur le texte officiel.',
            'effective_from': date(2018, 1, 1), 'verified': False})
        created = 0
        for code, label in ACCOUNTS:
            _, was_created = Account.objects.update_or_create(company=None, code=code, defaults={'label': label, 'version': version})
            created += was_created
        self.stdout.write(f'  Plan comptable : {len(ACCOUNTS)} comptes ({created} nouveaux)')

    def load_tax(self):
        for code, label, rate, source in TAX_RATES:
            TaxRate.objects.get_or_create(code=code, defaults={'label': label, 'rate': rate, 'source': source, 'verified': False})
        for rule_type, code, label, description, source in RULES:
            AccountingRule.objects.update_or_create(rule_type=rule_type, code=code, defaults={
                'label': label, 'description': description, 'source': source})
        self.stdout.write(f'  Taux fiscaux et règles : {len(TAX_RATES)} taux, {len(RULES)} règles')

    def load_catalog(self):
        n_chapters = 0
        for lvl in CATALOG:
            level, _ = ProgrammeLevel.objects.update_or_create(code=lvl['code'], defaults={'title': lvl['title'], 'description': lvl['description']})
            for m_order, mod in enumerate(lvl['modules'], start=1):
                module, _ = Module.objects.update_or_create(level=level, code=mod['code'], defaults={
                    'title': mod['title'], 'objectives': mod['objectives'], 'order': m_order})
                for c_order, (title, summary, formulas, slug) in enumerate(mod['chapters'], start=1):
                    chapter, _ = Chapter.objects.update_or_create(module=module, order=c_order, defaults={
                        'title': title, 'summary': summary, 'formulas': formulas, 'calculator_slug': slug})
                    Lesson.objects.get_or_create(chapter=chapter, order=1, defaults={
                        'title': title, 'objectives': f'Comprendre : {title.lower()}.', 'content': summary, 'formulas': formulas})
                    n_chapters += 1
        self.stdout.write(f'  Catalogue pédagogique : {Module.objects.count()} modules, {n_chapters} chapitres')

    def load_quizzes(self):
        for spec in QUIZZES:
            module = Module.objects.filter(level__code=spec['level'], code=spec['module']).first() if spec['module'] else None
            quiz, created = Quiz.objects.get_or_create(title=spec['title'], level=spec['level'], defaults={
                'module': module, 'kind': spec['kind'], 'duration_minutes': spec['duration'],
                'description': spec.get('description', '')})
            if not created:
                continue
            for order, q in enumerate(spec['questions'], start=1):
                kind = q[0]
                if kind == 'mcq':
                    _, text, choices, explanation, points = q
                    question = Question.objects.create(quiz=quiz, kind='mcq', text=text, explanation=explanation, points=points, order=order)
                    Choice.objects.bulk_create([Choice(question=question, text=t, is_correct=c) for t, c in choices])
                elif kind == 'num':
                    _, text, answer, tol, explanation, points = q
                    Question.objects.create(quiz=quiz, kind='numeric', text=text, explanation=explanation, points=points, order=order,
                                            answer_numeric=Decimal(answer), tolerance=Decimal(tol))
                else:
                    _, text, lines, explanation, points = q
                    Question.objects.create(quiz=quiz, kind='entry', text=text, explanation=explanation, points=points, order=order,
                                            expected_entry=[{'account': a, 'debit': d, 'credit': c} for a, d, c in lines])
        self.stdout.write(f'  Banque de quiz : {Quiz.objects.count()} quiz / examens')

    def load_demo(self):
        demo = [
            ('admin', 'admin@btcompta.ml', 'Admin', 'BT COMPTA', 'admin', True),
            ('enseignant', 'enseignant@btcompta.ml', 'Awa', 'Coulibaly', 'teacher', False),
            ('eleve', 'eleve@btcompta.ml', 'Moussa', 'Traoré', 'student', False),
            ('comptable', 'comptable@btcompta.ml', 'Fatoumata', 'Diallo', 'accountant', False),
        ]
        for username, email, first, last, role, superuser in demo:
            user, created = User.objects.get_or_create(username=username, defaults={
                'email': email, 'first_name': first, 'last_name': last, 'role': role, 'level': 'BT1' if role == 'student' else '',
                'is_staff': superuser, 'is_superuser': superuser})
            if created:
                user.set_password('BtCompta2026!')
                user.save()
        owner = User.objects.get(username='comptable')
        company, created = Company.objects.get_or_create(owner=owner, name='Boutique Sahel SARL', defaults={
            'legal_form': 'SARL', 'city': 'Bamako', 'is_training': True})
        create_default_journals(company)
        if created:
            fy = FiscalYear.objects.create(company=company, label='Exercice 2026', start_date=date(2026, 1, 1), end_date=date(2026, 12, 31))
            acc = {a.code: a for a in Account.objects.filter(company=None)}
            j = {x.code: x for x in Journal.objects.filter(company=company)}
            operations = [
                ('OD', date(2026, 1, 2), 'APP-01', 'Apport en capital', [('521', '5000000', '0'), ('101', '0', '5000000')]),
                ('AC', date(2026, 1, 8), 'FA-001', 'Achat de marchandises Ets Diallo',
                 [('601', '1200000', '0'), ('4452', '216000', '0'), ('401', '0', '1416000')]),
                ('VT', date(2026, 1, 15), 'FV-001', 'Vente de marchandises client Koné',
                 [('411', '1652000', '0'), ('701', '0', '1400000'), ('4431', '0', '252000')]),
                ('BQ', date(2026, 1, 20), 'CH-001', 'Règlement fournisseur Diallo', [('401', '1416000', '0'), ('521', '0', '1416000')]),
                ('BQ', date(2026, 1, 28), 'VIR-01', 'Règlement client Koné', [('521', '1652000', '0'), ('411', '0', '1652000')]),
                ('BQ', date(2026, 1, 31), 'REL-01', 'Frais bancaires de janvier', [('631', '7500', '0'), ('521', '0', '7500')]),
            ]
            for jcode, d, ref, label, lines in operations:
                entry = JournalEntry.objects.create(company=company, fiscal_year=fy, journal=j[jcode], date=d,
                                                    reference=ref, label=label, created_by=owner)
                EntryLine.objects.bulk_create([EntryLine(entry=entry, account=acc[a], label=label, debit=Decimal(dv), credit=Decimal(cv))
                                               for a, dv, cv in lines])
                validate_entry(entry, owner)
        self.stdout.write(self.style.WARNING(
            '  Comptes de démonstration (mot de passe : BtCompta2026!) : admin, enseignant, eleve, comptable — '
            'à supprimer ou modifier en production.'))
