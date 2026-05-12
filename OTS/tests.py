from django.contrib.auth.hashers import check_password, make_password
from django.test import TestCase
from rest_framework.test import APIClient

from OTS.models import Candidate, MembershipPlan, Question
from OTS import services


class SecurityHardeningTests(TestCase):
    def setUp(self):
        self.plan = MembershipPlan.objects.create(
            name='Basic',
            description='Basic plan',
            allowed_question_counts='1,3,5',
            is_active=True,
        )
        self.candidate = Candidate.objects.create(
            username='sachin',
            password=make_password('sachin'),
            name='Sachin',
            membership_plan=self.plan,
        )
        self.client = APIClient()

    def _login_candidate(self):
        response = self.client.post(
            '/OTS/api/candidates/login/',
            {'username': 'sachin', 'password': 'sachin'},
            format='json',
        )
        self.assertEqual(response.status_code, 200)
        token = response.data.get('access')
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')

    def test_register_hashes_password(self):
        ok, _ = services.register_candidate('u1', 'pass123', 'User One')
        self.assertTrue(ok)
        created = Candidate.objects.get(username='u1')
        self.assertNotEqual(created.password, 'pass123')
        self.assertTrue(check_password('pass123', created.password))

    def test_login_upgrades_legacy_plaintext_password(self):
        legacy = Candidate.objects.create(username='legacy', password='legacy123', name='Legacy')
        authenticated = services.authenticate_candidate('legacy', 'legacy123')
        self.assertIsNotNone(authenticated)
        legacy.refresh_from_db()
        self.assertNotEqual(legacy.password, 'legacy123')
        self.assertTrue(check_password('legacy123', legacy.password))

    def test_candidate_cannot_edit_restricted_fields(self):
        self._login_candidate()
        response = self.client.patch('/OTS/api/candidates/sachin/', {'points': 999}, format='json')
        self.assertEqual(response.status_code, 400)

    def test_question_answer_not_exposed_to_candidate(self):
        Question.objects.create(que='Q?', a='A1', b='B1', c='C1', d='D1', ans='A')
        self._login_candidate()
        response = self.client.get('/OTS/api/questions/')
        self.assertEqual(response.status_code, 200)
        payload = response.data['results'] if isinstance(response.data, dict) and 'results' in response.data else response.data
        self.assertTrue(payload)
        self.assertNotIn('ans', payload[0])
