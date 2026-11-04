"""Tests de sécurité : jetons, révocation, verrouillage, réinitialisation, droits d'administration, limites."""
import re

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core import mail
from django.core.cache import cache
from django.test import TestCase, override_settings
from rest_framework.test import APIClient

from core.models import AuditLog

User = get_user_model()
PASSWORD = 'Motdepasse-solide-2026'
COOKIE = settings.REFRESH_COOKIE['key']


class SecurityTestCase(TestCase):
    def setUp(self):
        cache.clear()  # remet à zéro les compteurs de limitation de débit
        self.user = User.objects.create_user('awa', 'awa@test.ml', PASSWORD, role='student')
        self.admin = User.objects.create_user('chef', 'chef@test.ml', PASSWORD, role='admin')

    def login(self, client=None, identifier='awa', password=PASSWORD):
        client = client or APIClient()
        return client, client.post('/api/auth/login/', {'identifier': identifier, 'password': password}, format='json')


class TokenTests(SecurityTestCase):
    def test_refresh_token_only_in_httponly_cookie(self):
        _, r = self.login()
        self.assertEqual(r.status_code, 200)
        self.assertIn('access', r.json())
        self.assertNotIn('refresh', r.json())  # jamais exposé au JavaScript
        cookie = r.cookies[COOKIE]
        self.assertTrue(cookie['httponly'])
        self.assertEqual(cookie['samesite'], 'Strict')
        self.assertEqual(cookie['path'], '/api/auth/')

    def test_native_clients_can_receive_refresh_in_body(self):
        r = APIClient().post('/api/auth/login/', {'identifier': 'awa', 'password': PASSWORD}, format='json',
                             HTTP_X_TOKEN_TRANSPORT='body')
        self.assertIn('refresh', r.json())

    def test_refresh_rotates_and_old_token_is_revoked(self):
        client, r = self.login()
        old = r.cookies[COOKIE].value
        r2 = client.post('/api/auth/refresh/')
        self.assertEqual(r2.status_code, 200)
        self.assertIn('access', r2.json())
        self.assertNotEqual(r2.cookies[COOKIE].value, old)
        replay = APIClient()
        replay.cookies[COOKIE] = old
        self.assertEqual(replay.post('/api/auth/refresh/').status_code, 401)

    def test_logout_revokes_refresh_token(self):
        client, r = self.login()
        token = r.cookies[COOKIE].value
        self.assertEqual(client.post('/api/auth/logout/').status_code, 204)
        replay = APIClient()
        replay.cookies[COOKIE] = token
        self.assertEqual(replay.post('/api/auth/refresh/').status_code, 401)

    def test_refresh_without_cookie(self):
        self.assertEqual(APIClient().post('/api/auth/refresh/').status_code, 401)

    def test_password_change_closes_other_sessions(self):
        other_device, r = self.login()
        other_token = r.cookies[COOKIE].value
        client, r = self.login()
        client.credentials(HTTP_AUTHORIZATION='Bearer ' + r.json()['access'])
        r = client.post('/api/auth/change-password/', {'old_password': PASSWORD, 'new_password': 'Nouveau-secret-2026'}, format='json')
        self.assertEqual(r.status_code, 200, r.content)
        replay = APIClient()
        replay.cookies[COOKIE] = other_token
        self.assertEqual(replay.post('/api/auth/refresh/').status_code, 401)
        self.assertEqual(client.post('/api/auth/refresh/').status_code, 200)  # la session courante continue

    def test_deactivated_user_cannot_refresh(self):
        client, _ = self.login()
        admin = APIClient()
        admin.force_authenticate(self.admin)
        admin.patch(f'/api/auth/users/{self.user.id}/', {'is_active': False}, format='json')
        self.assertEqual(client.post('/api/auth/refresh/').status_code, 401)


@override_settings(LOGIN_MAX_FAILURES=3, LOGIN_LOCK_MINUTES=15)
class LockoutTests(SecurityTestCase):
    def test_account_locked_after_repeated_failures(self):
        for _ in range(3):
            _, r = self.login(password='mauvais')
            self.assertEqual(r.status_code, 400)
        _, r = self.login()  # même le bon mot de passe est refusé pendant le verrouillage
        self.assertEqual(r.status_code, 403)
        self.assertIn('verrouillé', r.json()['detail'])
        self.assertTrue(AuditLog.objects.filter(action='auth.account_locked', target_id=str(self.user.id)).exists())

    def test_success_resets_counter(self):
        self.login(password='mauvais')
        self.login(password='mauvais')
        _, r = self.login()
        self.assertEqual(r.status_code, 200)
        self.user.refresh_from_db()
        self.assertEqual(self.user.failed_login_attempts, 0)

    def test_admin_can_unlock(self):
        for _ in range(3):
            self.login(password='mauvais')
        admin = APIClient()
        admin.force_authenticate(self.admin)
        self.assertEqual(admin.post(f'/api/auth/users/{self.user.id}/unlock/').status_code, 200)
        self.assertEqual(self.login()[1].status_code, 200)

    def test_unknown_user_same_message(self):
        _, r = self.login(identifier='inconnu')
        self.assertEqual(r.json()['detail'], 'Identifiants incorrects.')


class PasswordResetTests(SecurityTestCase):
    def test_full_reset_flow(self):
        r = APIClient().post('/api/auth/password-reset/', {'email': 'AWA@test.ml'}, format='json')
        self.assertEqual(r.status_code, 200)
        self.assertEqual(len(mail.outbox), 1)
        uid, token = re.search(r'uid=([\w-]+)&token=([\w-]+)', mail.outbox[0].body).groups()
        r = APIClient().post('/api/auth/password-reset/confirm/', {'uid': uid, 'token': token, 'new_password': 'Reinit-secret-2026'}, format='json')
        self.assertEqual(r.status_code, 200, r.content)
        self.assertEqual(self.login(password='Reinit-secret-2026')[1].status_code, 200)
        # Le lien ne fonctionne qu'une fois
        r = APIClient().post('/api/auth/password-reset/confirm/', {'uid': uid, 'token': token, 'new_password': 'Autre-secret-2026'}, format='json')
        self.assertEqual(r.status_code, 400)

    def test_unknown_email_gives_same_answer_and_no_mail(self):
        r1 = APIClient().post('/api/auth/password-reset/', {'email': 'personne@test.ml'}, format='json')
        r2 = APIClient().post('/api/auth/password-reset/', {'email': 'awa@test.ml'}, format='json')
        self.assertEqual(r1.json(), r2.json())
        self.assertEqual(len(mail.outbox), 1)

    def test_forged_token_rejected(self):
        r = APIClient().post('/api/auth/password-reset/confirm/', {'uid': 'MQ', 'token': 'faux-jeton', 'new_password': 'Reinit-secret-2026'}, format='json')
        self.assertEqual(r.status_code, 400)


class AdminProtectionTests(SecurityTestCase):
    def test_admin_cannot_demote_or_deactivate_self(self):
        c = APIClient()
        c.force_authenticate(self.admin)
        self.assertEqual(c.patch(f'/api/auth/users/{self.admin.id}/', {'role': 'student'}, format='json').status_code, 400)
        self.assertEqual(c.patch(f'/api/auth/users/{self.admin.id}/', {'is_active': False}, format='json').status_code, 400)

    def test_demoted_admin_loses_access(self):
        other = User.objects.create_user('chef2', 'chef2@test.ml', PASSWORD, role='admin')
        c = APIClient()
        c.force_authenticate(other)
        self.assertEqual(c.patch(f'/api/auth/users/{self.admin.id}/', {'role': 'teacher'}, format='json').status_code, 200)
        self.admin.refresh_from_db()
        c.force_authenticate(self.admin)  # ancien admin, désormais enseignant : n'a plus accès
        self.assertEqual(c.get('/api/auth/users/').status_code, 403)


class HardeningTests(SecurityTestCase):
    def setUp(self):
        super().setUp()
        self.c = APIClient()
        self.c.force_authenticate(self.user)

    def test_security_headers_on_api(self):
        r = self.c.get('/api/auth/me/')
        self.assertIn("default-src 'none'", r['Content-Security-Policy'])
        self.assertEqual(r['Cache-Control'], 'no-store')
        self.assertEqual(r['X-Frame-Options'], 'DENY')
        self.assertIn('camera=()', r['Permissions-Policy'])

    def test_calculator_row_limit(self):
        rows = [{'designation': 'x', 'quantity': '1', 'unit_price': '1'}] * (settings.CALC_MAX_TABLE_ROWS + 1)
        r = self.c.post('/api/calculations/facture/run/', {'inputs': {'lines': rows}}, format='json')
        self.assertEqual(r.status_code, 400)

    def test_absurd_amount_rejected(self):
        r = self.c.post('/api/calculations/tva/run/', {'inputs': {'amount': '9' * 30}}, format='json')
        self.assertEqual(r.status_code, 400)

    def test_invalid_id_parameter_is_400_not_500(self):
        self.assertEqual(self.c.get('/api/accounting/entries/?company=abc').status_code, 400)
        self.assertEqual(self.c.get('/api/exams/quizzes/?module=1;DROP').status_code, 400)

    def test_teacher_cannot_access_admin_endpoints(self):
        self.assertEqual(self.c.get('/api/audit-logs/').status_code, 403)
