import io
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient

from accounting.models import Account, JournalEntry
from examinations.models import Quiz

User = get_user_model()
PASSWORD = 'Motdepasse-solide-2026'


class BaseAPITest(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command('bootstrap_data', stdout=io.StringIO())
        cls.student = User.objects.create_user('eleve1', 'eleve1@test.ml', PASSWORD, role='student')
        cls.other = User.objects.create_user('eleve2', 'eleve2@test.ml', PASSWORD, role='student')
        cls.admin = User.objects.create_user('admin1', 'admin1@test.ml', PASSWORD, role='admin')
        cls.teacher = User.objects.create_user('prof1', 'prof1@test.ml', PASSWORD, role='teacher')

    def client_for(self, user):
        c = APIClient()
        c.force_authenticate(user)
        return c


class AuthTests(BaseAPITest):
    def test_ping_public(self):
        self.assertEqual(self.client.get(reverse('ping')).status_code, 200)

    def test_protected_requires_auth(self):
        self.assertEqual(self.client.get(reverse('dashboard')).status_code, 401)

    def test_register_and_login_by_email(self):
        c = APIClient()
        r = c.post(reverse('register'), {'username': 'nouveau', 'email': 'Nouveau@test.ml', 'first_name': 'A', 'last_name': 'B',
                                         'password': PASSWORD, 'level': 'BT2'}, format='json')
        self.assertEqual(r.status_code, 201, r.content)
        self.assertIn('access', r.json())
        self.assertEqual(r.json()['user']['role'], 'student')
        r = c.post(reverse('login'), {'identifier': 'nouveau@test.ml', 'password': PASSWORD}, format='json')
        self.assertEqual(r.status_code, 200, r.content)
        c.credentials(HTTP_AUTHORIZATION='Bearer ' + r.json()['access'])
        self.assertEqual(c.get(reverse('me')).json()['username'], 'nouveau')

    def test_cannot_self_register_as_admin(self):
        r = APIClient().post(reverse('register'), {'username': 'pirate', 'email': 'p@test.ml', 'first_name': 'A', 'last_name': 'B',
                                                   'password': PASSWORD, 'role': 'admin'}, format='json')
        self.assertEqual(r.status_code, 400)

    def test_weak_password_rejected(self):
        r = APIClient().post(reverse('register'), {'username': 'faible', 'email': 'f@test.ml', 'first_name': 'A', 'last_name': 'B',
                                                   'password': '123'}, format='json')
        self.assertEqual(r.status_code, 400)
        self.assertIn('password', r.json())

    def test_wrong_password(self):
        r = APIClient().post(reverse('login'), {'identifier': 'eleve1', 'password': 'faux'}, format='json')
        self.assertEqual(r.status_code, 400)

    def test_user_cannot_change_own_role(self):
        c = self.client_for(self.student)
        c.patch(reverse('me'), {'role': 'admin'}, format='json')
        self.student.refresh_from_db()
        self.assertEqual(self.student.role, 'student')

    def test_user_admin_is_admin_only(self):
        self.assertEqual(self.client_for(self.student).get('/api/auth/users/').status_code, 403)
        r = self.client_for(self.admin).patch(f'/api/auth/users/{self.other.id}/', {'role': 'teacher'}, format='json')
        self.assertEqual(r.status_code, 200)
        self.other.refresh_from_db()
        self.assertEqual(self.other.role, 'teacher')


class PedagogyTests(BaseAPITest):
    def test_catalog_has_10_bt1_and_8_bt2_modules(self):
        c = self.client_for(self.student)
        levels = {l['code']: l for l in c.get('/api/pedagogy/levels/').json()}
        self.assertEqual(len(levels['BT1']['modules']), 10)
        self.assertEqual(len(levels['BT2']['modules']), 8)

    def test_progress_and_student_cannot_edit(self):
        c = self.client_for(self.student)
        module = c.get('/api/pedagogy/modules/?level=BT1').json()[0]
        detail = c.get(f'/api/pedagogy/modules/{module["id"]}/').json()
        chapter_id = detail['chapters'][0]['id']
        self.assertEqual(c.post(f'/api/pedagogy/chapters/{chapter_id}/complete/').status_code, 200)
        self.assertEqual(c.get(f'/api/pedagogy/modules/{module["id"]}/').json()['completed_count'], 1)
        self.assertEqual(c.patch(f'/api/pedagogy/modules/{module["id"]}/', {'title': 'x'}, format='json').status_code, 403)
        self.assertEqual(self.client_for(self.teacher).patch(f'/api/pedagogy/modules/{module["id"]}/', {'objectives': 'ok'},
                                                             format='json').status_code, 200)


class CalculationAPITests(BaseAPITest):
    def test_catalog_and_run(self):
        c = self.client_for(self.student)
        items = c.get('/api/calculations/').json()
        self.assertGreaterEqual(len(items), 36)
        r = c.post('/api/calculations/tva/run/', {'inputs': {'amount': '100000', 'rate': '18'}, 'save': True}, format='json')
        self.assertEqual(r.status_code, 200)
        self.assertEqual(len(c.get('/api/calculations/history/').json()), 1)

    def test_run_error_message(self):
        r = self.client_for(self.student).post('/api/calculations/tva/run/', {'inputs': {'amount': 'abc'}}, format='json')
        self.assertEqual(r.status_code, 400)
        self.assertIn('detail', r.json())

    def test_exports(self):
        c = self.client_for(self.student)
        pdf = c.post('/api/calculations/facture/export/pdf/', {'inputs': {}}, format='json')
        self.assertEqual(pdf.status_code, 200)
        self.assertTrue(pdf.content.startswith(b'%PDF'))
        xlsx = c.post('/api/calculations/amortissement/export/xlsx/', {'inputs': {}}, format='json')
        self.assertEqual(xlsx.status_code, 200)
        self.assertTrue(xlsx.content.startswith(b'PK'))


class AccountingAPITests(BaseAPITest):
    def setUp(self):
        self.c = self.client_for(self.student)
        r = self.c.post('/api/accounting/companies/', {'name': 'Test SARL'}, format='json')
        self.assertEqual(r.status_code, 201, r.content)
        self.company = r.json()['id']
        r = self.c.post('/api/accounting/fiscal-years/', {'company': self.company, 'label': '2026',
                                                          'start_date': '2026-01-01', 'end_date': '2026-12-31'}, format='json')
        self.assertEqual(r.status_code, 201, r.content)
        self.fy = r.json()['id']
        self.journal = self.c.get(f'/api/accounting/journals/?company={self.company}').json()[0]['id']
        self.acc = {a.code: a.id for a in Account.objects.filter(company=None, code__in=['601', '4452', '401', '521', '701', '411', '4431'])}

    def entry(self, lines, d='2026-03-10'):
        return self.c.post('/api/accounting/entries/', {
            'company': self.company, 'fiscal_year': self.fy, 'journal': self.journal, 'date': d, 'reference': 'FA1',
            'label': 'Achat', 'lines': [{'account': self.acc[a], 'debit': dv, 'credit': cv} for a, dv, cv in lines]}, format='json')

    def test_default_journals_created(self):
        codes = {j['code'] for j in self.c.get(f'/api/accounting/journals/?company={self.company}').json()}
        self.assertEqual(codes, {'AC', 'VT', 'BQ', 'CA', 'OD'})

    def test_overlapping_fiscal_year_rejected(self):
        r = self.c.post('/api/accounting/fiscal-years/', {'company': self.company, 'label': 'bis',
                                                          'start_date': '2026-06-01', 'end_date': '2027-05-31'}, format='json')
        self.assertEqual(r.status_code, 400)

    def test_full_cycle_validation_lock_and_reversal(self):
        r = self.entry([('601', '300000', '0'), ('4452', '54000', '0'), ('401', '0', '354000')])
        self.assertEqual(r.status_code, 201, r.content)
        eid = r.json()['id']
        r = self.c.post(f'/api/accounting/entries/{eid}/validate/')
        self.assertEqual(r.status_code, 200, r.content)
        self.assertEqual(r.json()['number'], 1)
        # Une écriture validée n'est ni modifiable ni supprimable
        self.assertEqual(self.c.patch(f'/api/accounting/entries/{eid}/', {'label': 'modif'}, format='json').status_code, 400)
        self.assertEqual(self.c.delete(f'/api/accounting/entries/{eid}/').status_code, 400)
        tb = self.c.get(f'/api/accounting/companies/{self.company}/trial-balance/').json()
        self.assertTrue(tb['totals']['balanced'])
        self.assertEqual(Decimal(tb['totals']['debit']), Decimal('354000'))
        # Correction par contre-passation
        r = self.c.post(f'/api/accounting/entries/{eid}/reverse/', {'reason': 'erreur de montant'}, format='json')
        self.assertEqual(r.status_code, 201, r.content)
        self.assertEqual(r.json()['number'], 2)
        tb = self.c.get(f'/api/accounting/companies/{self.company}/trial-balance/').json()
        self.assertTrue(all(Decimal(row['balance_debit']) == 0 and Decimal(row['balance_credit']) == 0 for row in tb['rows']))
        self.assertEqual(self.c.post(f'/api/accounting/entries/{eid}/reverse/').status_code, 400)

    def test_unbalanced_entry_cannot_be_validated(self):
        r = self.entry([('601', '300000', '0'), ('401', '0', '200000')])
        eid = r.json()['id']
        r = self.c.post(f'/api/accounting/entries/{eid}/validate/')
        self.assertEqual(r.status_code, 400)
        self.assertEqual(JournalEntry.objects.get(pk=eid).status, 'draft')

    def test_date_outside_fiscal_year_rejected(self):
        r = self.entry([('601', '1000', '0'), ('401', '0', '1000')], d='2025-12-31')
        self.assertEqual(r.status_code, 400)

    def test_statements_balanced(self):
        for lines in ([('601', '500000', '0'), ('4452', '90000', '0'), ('401', '0', '590000')],
                      [('411', '826000', '0'), ('701', '0', '700000'), ('4431', '0', '126000')],
                      [('521', '826000', '0'), ('411', '0', '826000')]):
            eid = self.entry(lines).json()['id']
            self.assertEqual(self.c.post(f'/api/accounting/entries/{eid}/validate/').status_code, 200)
        inc = self.c.get(f'/api/accounting/companies/{self.company}/income-statement/').json()
        self.assertEqual(Decimal(inc['result']), Decimal('200000'))
        bs = self.c.get(f'/api/accounting/companies/{self.company}/balance-sheet/').json()
        self.assertTrue(bs['balanced'])
        self.assertEqual(Decimal(bs['total_actif']), Decimal('916000'))
        ledger = self.c.get(f'/api/accounting/companies/{self.company}/ledger/?account=411').json()
        self.assertEqual(Decimal(ledger[0]['balance']), Decimal('0'))
        pdf = self.c.get(f'/api/accounting/companies/{self.company}/trial-balance/?export=pdf')
        self.assertTrue(pdf.content.startswith(b'%PDF'))

    def test_other_user_cannot_see_company(self):
        other = self.client_for(self.other)
        self.assertEqual(other.get(f'/api/accounting/companies/{self.company}/').status_code, 404)
        r = other.post('/api/accounting/entries/', {'company': self.company, 'fiscal_year': self.fy, 'journal': self.journal,
                                                    'date': '2026-03-10', 'label': 'x', 'lines': []}, format='json')
        self.assertEqual(r.status_code, 400)


class ExamTests(BaseAPITest):
    def test_quiz_perfect_score_is_20(self):
        c = self.client_for(self.student)
        quiz = Quiz.objects.get(title='Factures, réductions et TVA')
        r = c.post(f'/api/exams/quizzes/{quiz.id}/start/')
        self.assertEqual(r.status_code, 201, r.content)
        data = r.json()
        self.assertNotIn('is_correct', str(data['questions']))  # les réponses ne fuient pas
        answers = {}
        for q in quiz.questions.prefetch_related('choices'):
            if q.kind == 'mcq':
                answers[str(q.id)] = [ch.id for ch in q.choices.all() if ch.is_correct]
            elif q.kind == 'numeric':
                answers[str(q.id)] = str(q.answer_numeric)
            else:
                answers[str(q.id)] = q.expected_entry
        r = c.post(f'/api/exams/attempts/{data["attempt"]}/submit/', {'answers': answers}, format='json')
        self.assertEqual(r.status_code, 200, r.content)
        self.assertEqual(Decimal(r.json()['grade']), Decimal('20'))
        self.assertEqual(c.post(f'/api/exams/attempts/{data["attempt"]}/submit/', {'answers': {}}, format='json').status_code, 400)

    def test_empty_answers_score_zero_and_progress(self):
        c = self.client_for(self.student)
        quiz = Quiz.objects.get(title='Gestion des stocks')
        attempt = c.post(f'/api/exams/quizzes/{quiz.id}/start/').json()['attempt']
        r = c.post(f'/api/exams/attempts/{attempt}/submit/', {'answers': {}}, format='json')
        self.assertEqual(Decimal(r.json()['grade']), Decimal('0'))
        progress = c.get('/api/exams/progress/').json()
        self.assertEqual(progress['by_level']['BT1']['n'], 1)
        self.assertTrue(progress['mistakes'])

    def test_partial_entry_grading(self):
        from examinations.grading import grade_question
        q = Quiz.objects.get(title='Partie double et documents comptables').questions.get(kind='entry')
        pts, ok, _ = grade_question(q, [{'account': '601', 'debit': '300000'}, {'account': '521', 'credit': '354000'}])
        self.assertFalse(ok)
        self.assertEqual(pts, Decimal('2.00'))  # 2 lignes justes sur 3 → 2/3 de 3 points

    def test_student_cannot_create_quiz(self):
        r = self.client_for(self.student).post('/api/exams/quizzes/', {'title': 'x', 'level': 'BT1'}, format='json')
        self.assertEqual(r.status_code, 403)


class DashboardTests(BaseAPITest):
    def test_dashboard_by_role(self):
        data = self.client_for(self.student).get('/api/dashboard/').json()
        self.assertEqual(data['levels']['BT1']['modules'], 10)
        self.assertNotIn('admin', data)
        self.assertIn('admin', self.client_for(self.admin).get('/api/dashboard/').json())
