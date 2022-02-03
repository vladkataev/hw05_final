from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import TestCase, Client
from django.urls import reverse
from http import HTTPStatus
from posts.models import Group, Post

User = get_user_model()


class PostURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='Username')
        cls.user2 = User.objects.create_user(username='author')
        cls.group = Group.objects.create(
            title='Тестовое название',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый текст',
            group=cls.group
        )
        cls.post2 = Post.objects.create(
            author=cls.user2,
            text='Тестовый текст второго усера'
        )

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.author_client = Client()
        self.author_client.force_login(self.user)

    def test_pages_for_all_users(self):
        """Страницы, доступные любому пользователю."""
        urls_for_all_users = {
            'posts:index': '',
            'posts:group_posts': {'slug': 'test-slug'},
            'posts:profile': {'username': 'Username'},
            'posts:post_detail': {'post_id': '1'},
        }
        for url, kwarg in urls_for_all_users.items():
            with self.subTest(url=url):
                response = self.guest_client.get(reverse(url, kwargs=kwarg))
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_post_create(self):
        """Страницы, доступные авторизованному пользователю."""
        urls_for_auth = {
            'posts:post_create': '',
            'posts:post_edit': {'post_id': '1'},
        }
        for url, kwarg in urls_for_auth.items():
            with self.subTest(url=url):
                response = self.authorized_client.get(
                    reverse(url, kwargs=kwarg)
                )
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_post_create_for_guest(self):
        """Запрет на создание поста не авторизованному пользователю."""
        response = self.guest_client.get(
            reverse('posts:post_create')
        )
        self.assertEqual(response.status_code, HTTPStatus.FOUND)

    def test_post_edit(self):
        """Страница posts/<int:post_id>/edit видна автору поста"""
        response = self.author_client.get(
            reverse('posts:post_edit', args=[self.post.id])
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_post_edit_for_others(self):
        """Страница posts/<int:post_id>/edit/ недоступна не автору поста"""
        response = self.authorized_client.get(
            reverse('posts:post_edit', kwargs={'post_id': '2'})
        )
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        self.assertRedirects(
            response,
            reverse('posts:post_detail', kwargs={'post_id': '2'})
        )

    def test_unexisting_page(self):
        """Запрос к несуществующей странице вернёт ошибку 404"""
        client_tipe = [self.guest_client, self.authorized_client]
        for client in client_tipe:
            response = client.get('/unexisting_page/')
            self.assertTemplateUsed(response, 'core/404.html')
            self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

    def test_post_urls_uses_correct_template(self):
        """URL-адресс приложения Post использует соответствующий шаблон"""
        cache.clear()
        templates_pages_names = {
            reverse(
                'posts:index'): 'posts/index.html',
            reverse(
                'posts:group_posts',
                kwargs={'slug': 'test-slug'}): 'posts/group_list.html',
            reverse(
                'posts:profile',
                kwargs={'username': 'Username'}): 'posts/profile.html',
            reverse(
                'posts:post_detail',
                kwargs={'post_id': '1'}): 'posts/post_detail.html',
            reverse(
                'posts:post_edit',
                kwargs={'post_id': '1'}): 'posts/create_post.html',
            reverse(
                'posts:post_create'): 'posts/create_post.html',
        }
        for url, kwarg in templates_pages_names.items():
            with self.subTest(url=url):
                response = self.author_client.get(url)
                self.assertTemplateUsed(response, kwarg)
