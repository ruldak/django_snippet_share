from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from snippets.models import Snippet
from django.contrib.auth.models import User


class SnippetCreationTests(APITestCase):
    def setUp(self):
        """
        The setUp method is run before each test.
        We create a user here to be used in all tests in this class.
        """
        self.user = User.objects.create_user(username='testuser', password='testpassword')
        self.list_create_url = reverse('snippet-list')

    def test_logged_in_user_can_create_snippet(self):
        """
        Test if a logged-in user can create a snippet.
        """
        self.client.force_authenticate(user=self.user)
        
        snippet_data = {
            'title': 'Test Snippet Title',
            'content': 'print("Hello, World!")',
            'language': 'python',
            'visibility': 'public'
        }

        response = self.client.post(self.list_create_url, snippet_data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        self.assertEqual(Snippet.objects.count(), 1)

        created_snippet = Snippet.objects.get()
        self.assertEqual(created_snippet.title, snippet_data['title'])
        self.assertEqual(created_snippet.user, self.user)

    def test_unauthenticated_user_cannot_create_snippet(self):
        """
        Test if an unauthenticated user cannot create a snippet.
        """
        snippet_data = {
            'title': 'Unauthorized Snippet',
            'content': 'foo = "bar"',
        }

        response = self.client.post(self.list_create_url, snippet_data, format='json')

        self.assertIn(response.status_code, [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN])

        self.assertEqual(Snippet.objects.count(), 0)


class SnippetAccessTests(APITestCase):
    def setUp(self):
        self.user_a = User.objects.create_user(username='userA', password='passwordA')
        self.user_b = User.objects.create_user(username='userB', password='passwordB')

        self.public_snippet_A = Snippet.objects.create(
            user=self.user_a, title='Public Snippet A', content='Public content', visibility='public')
        
        self.private_snippet_A = Snippet.objects.create(
            user=self.user_a, title='Private Snippet A', content='Private content', visibility='private')

    def test_create_snippet_with_invalid_data_fails(self):
        """Test snippet creation fails if the data is invalid (e.g., empty title)."""
        self.client.force_authenticate(user=self.user_a)
        invalid_data = {'title': '', 'content': 'some content'}
        response = self.client.post(reverse('snippet-list'), invalid_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_any_user_can_view_public_snippet(self):
        """Test any user (even anonymous) can view a public snippet."""
        detail_url = reverse('snippet-detail', kwargs={'pk': self.public_snippet_A.pk})
        response = self.client.get(detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['title'], self.public_snippet_A.title)

    def test_user_can_view_own_private_snippet(self):
        """Test a user can view their own private snippet."""
        self.client.force_authenticate(user=self.user_a)
        detail_url = reverse('snippet-detail', kwargs={'pk': self.private_snippet_A.pk})
        response = self.client.get(detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['title'], self.private_snippet_A.title)

    def test_user_cannot_view_another_users_private_snippet(self):
        """Test user B cannot view user A's private snippet."""
        self.client.force_authenticate(user=self.user_b)
        detail_url = reverse('snippet-detail', kwargs={'pk': self.private_snippet_A.pk})
        response = self.client.get(detail_url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_user_cannot_edit_another_users_snippet(self):
        """Test user B cannot edit user A's snippet."""
        self.client.force_authenticate(user=self.user_b)
        detail_url = reverse('snippet-detail', kwargs={'pk': self.public_snippet_A.pk})
        update_data = {'title': 'New Title by B', 'content': 'hacked'}
        response = self.client.put(detail_url, update_data, format='json')
        self.assertIn(response.status_code, [status.HTTP_403_FORBIDDEN, status.HTTP_404_NOT_FOUND])

    def test_user_cannot_delete_another_users_snippet(self):
        """Test user B cannot delete user A's snippet."""
        self.client.force_authenticate(user=self.user_b)
        detail_url = reverse('snippet-detail', kwargs={'pk': self.public_snippet_A.pk})
        response = self.client.delete(detail_url)
        self.assertIn(response.status_code, [status.HTTP_403_FORBIDDEN, status.HTTP_404_NOT_FOUND])
        self.assertTrue(Snippet.objects.filter(pk=self.public_snippet_A.pk).exists())