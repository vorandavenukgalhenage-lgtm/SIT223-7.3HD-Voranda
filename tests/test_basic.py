from django.test import TestCase
from django.contrib.auth import get_user_model
from home.models import Article

User = get_user_model()


class BasicPageTests(TestCase):
    """Sanity checks that key pages load."""

    def test_homepage_loads(self):
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)

    def test_admin_page_exists(self):
        response = self.client.get('/admin/')
        self.assertIn(response.status_code, [200, 301, 302])


class UserCRUDTests(TestCase):
    """Tests real Create/Read/Update/Delete on the User model.
    Note: this project's custom User model uses email as the login identifier,
    with no username field at all."""

    def test_create_user(self):
        user = User.objects.create_user(
            email='testcrud1@example.com',
            password='TestPass123!',
            first_name='Test',
            last_name='UserOne',
            is_verified=True,
            is_active=True
        )
        self.assertEqual(User.objects.filter(email='testcrud1@example.com').count(), 1)

    def test_read_user(self):
        User.objects.create_user(
            email='readme@example.com',
            password='TestPass123!',
            first_name='Read',
            last_name='Me'
        )
        found = User.objects.get(email='readme@example.com')
        self.assertEqual(found.first_name, 'Read')

    def test_update_user(self):
        user = User.objects.create_user(
            email='updateme@example.com',
            password='TestPass123!',
            first_name='Old',
            last_name='Name'
        )
        user.first_name = 'New'
        user.save()
        refreshed = User.objects.get(email='updateme@example.com')
        self.assertEqual(refreshed.first_name, 'New')

    def test_delete_user(self):
        user = User.objects.create_user(
            email='deleteme@example.com',
            password='TestPass123!',
            first_name='Delete',
            last_name='Me'
        )
        user_id = user.id
        user.delete()
        self.assertFalse(User.objects.filter(id=user_id).exists())


class ArticleCRUDTests(TestCase):
    """Tests real Create/Read/Update/Delete on the Article model.
    Note: 'date' is auto_now_add=True, so it must never be passed in manually —
    Django sets it automatically and silently ignores any value you try to supply."""

    def setUp(self):
        # Article.author is a required ForeignKey, so we need a User to own the articles
        self.author = User.objects.create_user(
            email='author@example.com',
            password='TestPass123!',
            first_name='Author',
            last_name='Person'
        )

    def test_create_article(self):
        article = Article.objects.create(
            title='Test Article',
            content='Some content here',
            author=self.author
        )
        self.assertEqual(Article.objects.filter(title='Test Article').count(), 1)

    def test_read_article(self):
        Article.objects.create(
            title='Readable Article',
            content='Content here',
            author=self.author
        )
        found = Article.objects.get(title='Readable Article')
        self.assertEqual(found.content, 'Content here')

    def test_update_article(self):
        article = Article.objects.create(
            title='Old Title',
            content='Content',
            author=self.author
        )
        article.title = 'New Title'
        article.save()
        refreshed = Article.objects.get(id=article.id)
        self.assertEqual(refreshed.title, 'New Title')

    def test_delete_article(self):
        article = Article.objects.create(
            title='Delete Me',
            content='Content',
            author=self.author
        )
        article_id = article.id
        article.delete()
        self.assertFalse(Article.objects.filter(id=article_id).exists())