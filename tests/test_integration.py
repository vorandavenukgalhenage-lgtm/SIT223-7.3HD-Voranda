from django.contrib.auth import get_user_model
from django.test import TestCase

User = get_user_model()


class PublicPageIntegrationTests(TestCase):
    """Real HTTP requests through URL routing, middleware, views and templates."""

    def test_homepage_returns_ok(self):
        self.assertEqual(self.client.get('/').status_code, 200)

    def test_admin_login_page_available(self):
        self.assertEqual(self.client.get('/admin/login/').status_code, 200)

    def test_admin_requires_authentication(self):
        response = self.client.get('/admin/')
        self.assertEqual(response.status_code, 302)
        self.assertIn('/admin/login/', response['Location'])


class AuthenticatedIntegrationTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email='integration@example.com', password='TestPass123!',
            first_name='Int', last_name='Test', is_verified=True, is_active=True)

    def test_password_is_hashed(self):
        self.assertNotEqual(self.user.password, 'TestPass123!')

    def test_password_check(self):
        self.assertTrue(self.user.check_password('TestPass123!'))
        self.assertFalse(self.user.check_password('wrong-password'))

    def test_staff_user_can_log_in_to_admin(self):
        User.objects.create_user(
            email='staff@example.com', password='TestPass123!',
            first_name='Staff', last_name='User', is_verified=True,
            is_active=True, is_staff=True, is_superuser=True)
        response = self.client.post(
            '/admin/login/?next=/admin/',
            {'username': 'staff@example.com', 'password': 'TestPass123!'})
        self.assertEqual(response.status_code, 302)
        self.assertEqual(self.client.get('/admin/').status_code, 200)