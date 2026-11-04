"""Inscription professionnelle (validation des enseignants) et sujets d'examen avec corrigés."""
import shutil
import tempfile

from django.contrib.auth import get_user_model
from django.core import mail
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from rest_framework.test import APIClient

User = get_user_model()
PASSWORD = 'Motdepasse-solide-2026'
PDF = b'%PDF-1.4\n1 0 obj<<>>endobj\ntrailer<<>>\n%%EOF'


def pro_payload(role, **extra):
    data = {'username': f'pro_{role}', 'email': f'{role}@ecole.ml', 'first_name': 'Awa', 'last_name': 'Keita', 'role': role,
            'phone': '+22370000000', 'establishment': 'Lycée technique de Bamako', 'password': PASSWORD}
    data.update(extra)
    return data


class ProRegistrationTests(TestCase):
    def setUp(self):
        cache.clear()
        self.admin = User.objects.create_user('chef', 'chef@test.ml', PASSWORD, role='admin')

    def test_accountant_is_active_immediately(self):
        r = APIClient().post('/api/auth/register/pro/', pro_payload('accountant'), format='json')
        self.assertEqual(r.status_code, 201, r.content)
        self.assertIn('access', r.json())
        self.assertEqual(r.json()['user']['role'], 'accountant')

    def test_teacher_requires_details(self):
        r = APIClient().post('/api/auth/register/pro/', pro_payload('teacher'), format='json')
        self.assertEqual(r.status_code, 400)
        self.assertIn('speciality', r.json())

    def test_teacher_pending_until_admin_approves(self):
        r = APIClient().post('/api/auth/register/pro/', pro_payload(
            'teacher', speciality='Comptabilité générale', motivation='Professeur de comptabilité en classes BT1 et BT2 depuis 6 ans.'), format='json')
        self.assertEqual(r.status_code, 202, r.content)
        self.assertNotIn('access', r.json())
        teacher = User.objects.get(username='pro_teacher')
        self.assertFalse(teacher.is_active)
        self.assertEqual(teacher.approval_status, 'pending')
        self.assertEqual(len(mail.outbox), 2)  # administrateurs + accusé de réception

        r = APIClient().post('/api/auth/login/', {'identifier': 'pro_teacher', 'password': PASSWORD}, format='json')
        self.assertEqual(r.status_code, 403)
        self.assertIn('validation', r.json()['detail'])
        # Mauvais mot de passe : pas d'information sur l'état du compte
        r = APIClient().post('/api/auth/login/', {'identifier': 'pro_teacher', 'password': 'faux'}, format='json')
        self.assertEqual(r.json()['detail'], 'Identifiants incorrects.')

        admin = APIClient()
        admin.force_authenticate(self.admin)
        pending = admin.get('/api/auth/users/?approval=pending').json()
        self.assertEqual([u['username'] for u in pending], ['pro_teacher'])
        self.assertEqual(admin.post(f'/api/auth/users/{teacher.id}/approve/').status_code, 200)
        r = APIClient().post('/api/auth/login/', {'identifier': 'pro_teacher', 'password': PASSWORD}, format='json')
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()['user']['role'], 'teacher')

    def test_rejected_teacher_sees_reason(self):
        APIClient().post('/api/auth/register/pro/', pro_payload(
            'teacher', speciality='Compta', motivation='Je souhaite enseigner la comptabilité analytique.'), format='json')
        teacher = User.objects.get(username='pro_teacher')
        admin = APIClient()
        admin.force_authenticate(self.admin)
        admin.post(f'/api/auth/users/{teacher.id}/reject/', {'note': 'Établissement non vérifiable'}, format='json')
        r = APIClient().post('/api/auth/login/', {'identifier': 'pro_teacher', 'password': PASSWORD}, format='json')
        self.assertEqual(r.status_code, 403)
        self.assertIn('Établissement non vérifiable', r.json()['detail'])

    def test_admin_role_never_self_assignable(self):
        for url in ('/api/auth/register/', '/api/auth/register/pro/'):
            r = APIClient().post(url, pro_payload('admin', speciality='x', motivation='x' * 30), format='json')
            self.assertEqual(r.status_code, 400)

    def test_student_register_no_longer_accepts_accountant(self):
        r = APIClient().post('/api/auth/register/', {**pro_payload('accountant')}, format='json')
        self.assertEqual(r.status_code, 400)


MEDIA = tempfile.mkdtemp()


@override_settings(MEDIA_ROOT=MEDIA)
class ExamSubjectTests(TestCase):
    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(MEDIA, ignore_errors=True)

    def setUp(self):
        cache.clear()
        self.teacher = User.objects.create_user('prof', 'prof@test.ml', PASSWORD, role='teacher')
        self.other_teacher = User.objects.create_user('prof2', 'prof2@test.ml', PASSWORD, role='teacher')
        self.student = User.objects.create_user('eleve', 'eleve@test.ml', PASSWORD, role='student', first_name='Moussa', last_name='Traoré')
        self.t = APIClient()
        self.t.force_authenticate(self.teacher)
        self.s = APIClient()
        self.s.force_authenticate(self.student)

    def upload(self, **extra):
        data = {'title': 'Examen blanc BT1 — Juin', 'level': 'BT1', 'kind': 'mock', 'total_points': '40',
                'subject_file': SimpleUploadedFile('sujet.pdf', PDF, content_type='application/pdf'),
                'correction_text': 'Exercice 1 : 601 D 500 000 / 401 C 590 000…'}
        data.update(extra)
        return self.t.post('/api/exams/subjects/', data, format='multipart')

    def test_full_flow_upload_view_correct_grade_results(self):
        r = self.upload(correction_file=SimpleUploadedFile('corrige.pdf', PDF, content_type='application/pdf'))
        self.assertEqual(r.status_code, 201, r.content)
        sid = r.json()['id']

        listing = self.s.get('/api/exams/subjects/?level=BT1').json()
        self.assertEqual(listing[0]['correction_text'], '')  # corrigé caché avant publication
        f = self.s.get(f'/api/exams/subjects/{sid}/subject-file/')
        self.assertEqual(f.status_code, 200)
        self.assertEqual(b''.join(f.streaming_content), PDF)
        self.assertEqual(self.s.post(f'/api/exams/subjects/{sid}/correct/').status_code, 403)
        self.assertEqual(self.s.get(f'/api/exams/subjects/{sid}/correction-file/').status_code, 403)

        r = self.t.post(f'/api/exams/subjects/{sid}/release-correction/', {'released': True}, format='json')
        self.assertTrue(r.json()['correction_released'])

        r = self.s.post(f'/api/exams/subjects/{sid}/correct/')
        self.assertEqual(r.status_code, 200)
        self.assertIn('601 D', r.json()['correction_text'])
        self.assertEqual(self.s.get(f'/api/exams/subjects/{sid}/correction-file/').status_code, 200)
        r = self.s.post(f'/api/exams/subjects/{sid}/grade/', {'grade': '30'}, format='json')
        self.assertEqual(r.json()['self_grade'], '15.00')  # 30/40 ramené sur 20
        self.assertEqual(self.s.post(f'/api/exams/subjects/{sid}/grade/', {'grade': '45'}, format='json').status_code, 400)

        res = self.t.get(f'/api/exams/subjects/{sid}/results/').json()
        self.assertEqual(res['summary']['corrected'], 1)
        self.assertEqual(res['summary']['average'], '15.00')
        self.assertEqual(res['rows'][0]['student'], 'Moussa Traoré')
        self.assertEqual(self.s.get(f'/api/exams/subjects/{sid}/results/').status_code, 403)

    def test_students_cannot_upload(self):
        r = self.s.post('/api/exams/subjects/', {'title': 'x', 'level': 'BT1',
                                                 'subject_file': SimpleUploadedFile('s.pdf', PDF)}, format='multipart')
        self.assertEqual(r.status_code, 403)

    def test_disguised_file_rejected(self):
        r = self.upload(subject_file=SimpleUploadedFile('virus.pdf', b'MZ\x90\x00 programme', content_type='application/pdf'))
        self.assertEqual(r.status_code, 400)
        r = self.upload(subject_file=SimpleUploadedFile('script.html', b'<script>alert(1)</script>', content_type='text/html'))
        self.assertEqual(r.status_code, 400)

    @override_settings(MAX_UPLOAD_MB=1)
    def test_size_limit(self):
        big = PDF + b'0' * (1024 * 1024 + 10)
        self.assertEqual(self.upload(subject_file=SimpleUploadedFile('gros.pdf', big)).status_code, 400)

    def test_only_author_can_edit_or_delete(self):
        sid = self.upload().json()['id']
        other = APIClient()
        other.force_authenticate(self.other_teacher)
        self.assertEqual(other.patch(f'/api/exams/subjects/{sid}/', {'title': 'pirate'}, format='json').status_code, 403)
        self.assertEqual(other.delete(f'/api/exams/subjects/{sid}/').status_code, 403)
        self.assertEqual(self.t.delete(f'/api/exams/subjects/{sid}/').status_code, 204)

    def test_cannot_release_without_correction(self):
        sid = self.upload(correction_text='').json()['id']
        self.assertEqual(self.t.post(f'/api/exams/subjects/{sid}/release-correction/', {'released': True}, format='json').status_code, 400)

    def test_unpublished_subject_hidden_from_students(self):
        sid = self.upload(is_published='false').json()['id']
        self.assertEqual(self.s.get(f'/api/exams/subjects/{sid}/').status_code, 404)
        self.assertEqual(self.s.get(f'/api/exams/subjects/{sid}/subject-file/').status_code, 404)
