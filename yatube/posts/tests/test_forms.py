import shutil
import tempfile

from django.contrib.auth import get_user_model
from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, override_settings, TestCase
from django.urls import reverse
from http import HTTPStatus
from posts.forms import PostForm
from ..models import Comment, Group, Post

User = get_user_model()
TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostCreateFormTests(TestCase):
    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='author')
        cls.group = Group.objects.create(
            title='Тестовый заголовок',
            slug='test-slug',
            description='Тестовое описание группы',
        )
        cls.group2 = Group.objects.create(
            title='Тестовый заголовок другой группы',
            slug='test-slug2',
            description='Тестовое описание группы 2',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый текст',
            group=cls.group
        )
        cls.form = PostForm()

        cls.comment = Comment.objects.create(
            post=cls.post,
            author=cls.user,
            text='Молодец пиши ещё!'
        )

    def setUp(self):
        self.guest_client = Client()
        self.author_client = Client()
        self.author_client.force_login(self.user)
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_create_post(self):
        """Валидная форма создает новую запись в базе данных"""
        post_count = Post.objects.count()
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x01\x00'
            b'\x01\x00\x00\x00\x00\x21\xf9\x04'
            b'\x01\x0a\x00\x01\x00\x2c\x00\x00'
            b'\x00\x00\x01\x00\x01\x00\x00\x02'
            b'\x02\x4c\x01\x00\x3b'
        )
        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif',
        )
        form_data = {
            'text': 'Тестовый текст о важном',
            'group': self.group.id,
            'image': uploaded,
        }
        response = self.author_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True,
        )
        self.assertRedirects(
            response, reverse('posts:profile', args=[self.user.username]))
        self.assertEqual(Post.objects.count(), post_count + 1)
        self.assertTrue(
            Post.objects.filter(
                text='Тестовый текст о важном',
                author=self.user,
                group=self.group.id,
                image=self.post.image
            ).exists()
        )

    def test_post_edit(self):
        """Валидная форма изменяет пост в базе данных"""
        post_count = Post.objects.count()
        group_post_count = self.group.posts.count()
        form_data = {
            'text': '— Eh bien, mon prince. Gênes et Lucques'
                    'ne sont plus que des apanages,'
                    'des поместья, de la famille Buonaparte',
            'group': self.group2.id
        }
        response = self.author_client.post(
            reverse('posts:post_edit', args=[self.post.id]),
            data=form_data,
            follow=True,
        )
        self.assertRedirects(
            response, reverse('posts:post_detail', args=[self.post.id]))
        self.assertEqual(self.group.posts.count(), group_post_count - 1)
        self.assertEqual(Post.objects.count(), post_count)
        self.assertTrue(
            Post.objects.filter(
                text='— Eh bien, mon prince. Gênes et Lucques'
                'ne sont plus que des apanages,'
                'des поместья, de la famille Buonaparte',
                author=self.user,
                group=self.group2.id
            ).exists()
        )

    def test_create_and_edit_post_guest_client(self):
        """Неавторизованный пользователь может только читать"""
        post_count = Post.objects.count()
        test_urls = (reverse('posts:post_create'),
                     reverse('posts:post_edit', args=[self.post.id])
                     )
        form_data = {
            'text': 'Анонимный ругательный пост',
            'group': self.group2.id
        }
        for url in test_urls:
            with self.subTest(url=url):
                response = self.guest_client.get(
                    url,
                    data=form_data,
                    follow=False
                )
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        self.assertEqual(Post.objects.count(), post_count)

    def test_comment_form(self):
        """Валидная форма создает комментарий"""
        comment_count = Comment.objects.count()
        form_data = {
            'post': self.post,
            'author': self.authorized_client,
            'text': 'Класс. Жду продолжения',
        }
        response = self.authorized_client.post(
            reverse('posts:add_comment', args=[self.post.id]),
            data=form_data,
            follow=True
        )
        self.assertRedirects(
            response, reverse('posts:post_detail', args=[self.post.id])
        )
        self.assertTrue(Comment.objects.filter(
            post=self.post,
            author=self.user,
            text='Класс. Жду продолжения'
        ).exists())
        self.assertEqual(Comment.objects.count(), comment_count + 1)
