from django.contrib.auth.hashers import check_password, make_password
from django.test import TestCase
from rest_framework.test import APIClient
import secrets

from OTS.models import Candidate, MembershipPlan, Question
from OTS import services


class SecurityHardeningTests(TestCase):
    def setUp(self):
        self.login_username = 'sachin'
        self.login_password = f"fixture-{secrets.token_hex(12)}"
        self.plan = MembershipPlan.objects.create(
            name='Basic',
            description='Basic plan',
            allowed_question_counts='1,3,5',
            is_active=True,
        )
        self.candidate = Candidate.objects.create(
            username=self.login_username,
            password=make_password(self.login_password),
            name='Sachin',
            membership_plan=self.plan,
        )
        self.client = APIClient()

    def _login_candidate(self):
        response = self.client.post(
            '/OTS/api/candidates/login/',
            {'username': self.login_username, 'password': self.login_password},
            format='json',
        )
        self.assertEqual(response.status_code, 200)
        token = response.data.get('access')
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')

    def test_register_hashes_password(self):
        register_password = f"fixture-{secrets.token_hex(12)}"
        ok, _ = services.register_candidate('u1', register_password, 'User One')
        self.assertTrue(ok)
        created = Candidate.objects.get(username='u1')
        self.assertNotEqual(created.password, register_password)
        self.assertTrue(check_password(register_password, created.password))

    def test_login_upgrades_legacy_plaintext_password(self):
        legacy_password = f"fixture-{secrets.token_hex(12)}"
        legacy = Candidate.objects.create(username='legacy', password=legacy_password, name='Legacy')
        authenticated = services.authenticate_candidate('legacy', legacy_password)
        self.assertIsNotNone(authenticated)
        legacy.refresh_from_db()
        self.assertNotEqual(legacy.password, legacy_password)
        self.assertTrue(check_password(legacy_password, legacy.password))

    def test_candidate_cannot_edit_restricted_fields(self):
        self._login_candidate()
        response = self.client.patch(f"/OTS/api/candidates/{self.login_username}/", {'points': 999}, format='json')
        self.assertEqual(response.status_code, 400)

    def test_question_answer_not_exposed_to_candidate(self):
        Question.objects.create(que='Q?', a='A1', b='B1', c='C1', d='D1', ans='A')
        self._login_candidate()
        response = self.client.get('/OTS/api/questions/')
        self.assertEqual(response.status_code, 200)
        payload = response.data['results'] if isinstance(response.data, dict) and 'results' in response.data else response.data
        self.assertTrue(payload)
        self.assertNotIn('ans', payload[0])
