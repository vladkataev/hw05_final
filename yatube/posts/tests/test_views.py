from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, Client
from django.urls import reverse
from django import forms
from posts.models import Comment, Follow, Group, Post
from posts.views import COUNT_POSTS

User = get_user_model()


class PostURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='author')
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
        cls.group = Group.objects.create(
            title='Тестовое название',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый текст',
            group=cls.group,
            image=uploaded,
        )
        cls.post2 = Post.objects.create(
            author=cls.user,
            text='Тестовый текст второго поста',
            group=cls.group
        )

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.author_client = Client()
        self.author_client.force_login(self.user)

    def test_posts_pages_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        cache.clear()
        templates_pages_names = {
            reverse('posts:index'): 'posts/index.html',
            reverse('posts:post_create'): 'posts/create_post.html',
            reverse(
                'posts:group_posts', args=[self.group.slug]
            ): 'posts/group_list.html',
            reverse(
                'posts:profile', args=[self.user.username]
            ): 'posts/profile.html',
            reverse(
                'posts:post_detail', args=[self.post.id]
            ): 'posts/post_detail.html',
            reverse(
                'posts:post_edit', args=[self.post.id]
            ): 'posts/create_post.html',
        }
        for reverse_name, template in templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_post_index_page_show_correct_context(self):
        """Шаблон post:index сформирован с правильным контекстом"""
        cache.clear()
        response = self.guest_client.get(reverse('posts:index'))
        object = response.context['page_obj'][0]
        context_objects = {
            self.user: object.author,
            self.group: object.group
        }
        for context, expected in context_objects.items():
            with self.subTest(context=context):
                self.assertEqual(expected, context)

    def test_group_posts_page_show_correct_context(self):
        """Шаблон post:group_posts сформирован с правильным контекстом"""
        response = self.guest_client.get(
            reverse('posts:group_posts', args=[self.group.slug]))
        for post in response.context['page_obj']:
            self.assertEqual(post.group, self.group)

    def test_post_profile_page_show_correct_context(self):
        """Шаблон post:profile сформирован с правильным контекстом"""
        response = self.guest_client.get(
            reverse('posts:profile', args=[self.user.username]))
        for post in response.context['page_obj']:
            self.assertEqual(post.author, self.user)

    def test_post_detail_page_show_correct_context(self):
        """Шаблон posts:post_detail сформирован с правильным контекстом"""
        response = self.guest_client.get(
            reverse('posts:post_detail', args=[self.post.id]))
        current_object = response.context['post']
        post_id = current_object.id
        self.assertEqual(post_id, self.post.id)

    def test_create_post_show_correct_context(self):
        """Шаблон post:post_create сформирован с правильным контекстом"""
        response = self.author_client.get(reverse('posts:post_create'))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.models.ModelChoiceField,
            'image': forms.fields.ImageField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_edit_post_show_correct_context(self):
        """Шаблон post:post_edit сформирован с правильным контекстом"""
        response = self.author_client.get(
            reverse('posts:post_edit', args=[self.post.id]))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.models.ModelChoiceField,
            'image': forms.fields.ImageField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                is_edit_field = response.context.get('is_edit')
                self.assertIsInstance(form_field, expected)
                self.assertEqual(is_edit_field, True)


COUNT_POSTS_2: int = 3  # число тестовых постов на второй странице


class PaginatorViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='author')
        cls.group = Group.objects.create(
            title='Тестовое название',
            slug='test-slug',
            description='Тестовое описание',
        )
        for numbers in range(COUNT_POSTS_2 + COUNT_POSTS):
            cls.post = Post.objects.create(
                author=cls.user,
                text=f'Тестовый текст {numbers}',
                group=cls.group,
            )

    def setUp(self):
        self.author_client = Client()
        self.author_client.force_login(self.user)
        self.guest_client = Client()
        self.pages_names = {
            'posts:group_posts': self.group.slug,
            'posts:profile': self.user.username,
        }
        cache.clear()

    def test_first_page_contains_ten_records_in_index(self):
        """Первая страница в index содержит 10 постов"""
        response = self.guest_client.get(reverse('posts:index'))
        self.assertEqual(len(response.context['page_obj']), COUNT_POSTS)

    def test_second_page_contains_three_records_in_index(self):
        """Вторая страница в index содержит 3 поста"""
        response = self.guest_client.get(reverse('posts:index') + '?page=2')
        self.assertEqual(len(response.context['page_obj']), COUNT_POSTS_2)

    def test_first_page_contains_ten_records_in_group_and_profile(self):
        """Первая страница в group и profile содержит 10 постов"""
        for adress, args in self.pages_names.items():
            with self.subTest(adress=adress):
                response = self.guest_client.get(reverse(adress, args=[args]))
                self.assertEqual(
                    len(response.context['page_obj']), COUNT_POSTS)

    def test_second_page_contains_three_records_in_group_and_profile(self):
        """Вторая страница в group и profile содержит 3 поста"""
        for adress, args in self.pages_names.items():
            with self.subTest(adress=adress):
                response = self.guest_client.get(
                    reverse(adress, args=[args]) + '?page=2')
                self.assertEqual(
                    len(response.context['page_obj']), COUNT_POSTS_2)


class CommentsViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='Pushkin')
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый текст',
        )
        cls.comment = Comment.objects.create(
            post=cls.post,
            author=cls.user,
            text='Тестовый комментарий'
        )

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_post_detail_contains_comment(self):
        """Комментарий появляется на странице поста."""
        response = self.client.get(
            reverse('posts:post_detail', kwargs={'post_id': '1'})
        )
        self.assertEqual(
            str(response.context['comments'][0].author), 'Pushkin'
        )
        self.assertEqual(
            response.context['comments'][0].text, 'Тестовый комментарий'
        )

    def test_auth_add_comment(self):
        """Авторизованный пользователь добавляет комментарий."""
        comment_count = Comment.objects.count()
        form_data = {
            'post': self.post,
            'author': self.authorized_client,
            'text': 'Тестовый комментарий 2',
        }
        self.authorized_client.post(
            reverse('posts:add_comment', args=[self.post.id]),
            data=form_data,
            follow=True
        )
        self.assertEqual(Comment.objects.count(), comment_count + 1)

    def test_anon_add_comment(self):
        """Запрет на добавление комментария анонимному пользователю."""
        comment_count = Comment.objects.count()
        form_data = {
            'post': self.post,
            'author': self.user,
            'text': 'Тестовый комментарий 3',
        }
        self.guest_client.post(
            reverse('posts:add_comment', args=[self.post.id]),
            data=form_data,
            follow=True
        )
        self.assertEqual(Comment.objects.count(), comment_count)


class CacheTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create_user(username='Leo')
        cls.author_client = Client()
        cls.post = Post.objects.create(
            author=cls.author,
            text='Тестовый текст',
        )

    def test_cache_index_page(self):
        """Проверка кеширования главной страницы"""
        response = self.author_client.get(reverse('posts:index'))
        count_posts = Post.objects.count()
        self.assertEqual(len(response.context['page_obj']), count_posts)
        self.post.delete()
        cache.clear()
        response2 = self.author_client.get(reverse('posts:index'))
        self.assertNotEqual(len(response.context['page_obj']), len(
            response2.context['page_obj']))


class FollowTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user1 = User.objects.create_user(username='Username')
        cls.user2 = User.objects.create_user(username='User')
        cls.author = User.objects.create_user(username='Author')
        cls.post1 = Post.objects.create(
            author=cls.author,
            text='Тестовый текст',
        )
        cls.follow = Follow.objects.create(
            user=cls.user2,
            author=cls.author
        )

    def setUp(self):
        self.authorized_client1 = Client()
        self.authorized_client1.force_login(self.user1)
        self.authorized_client2 = Client()
        self.authorized_client2.force_login(self.user2)
        cache.clear()

    def test_auth_follow(self):
        """Авторизованный пользователь может подписаться на автора"""
        follow_count = Follow.objects.count()
        response = self.authorized_client1.get(
            reverse(
                'posts:profile_follow',
                kwargs={'username': 'Author'}
            )
        )
        self.assertRedirects(
            response,
            reverse('posts:profile', kwargs={'username': 'Author'})
        )
        self.assertEqual(Follow.objects.count(), follow_count + 1)
        self.assertEqual(
            Follow.objects.get(id=2).author, self.author
        )
        self.assertEqual(
            Follow.objects.get(id=2).user, self.user1
        )

    def test_auth_unfollow(self):
        """Авторизованный пользователь может отписаться от автора"""
        follow_count = Follow.objects.count()
        response = self.authorized_client2.get(
            reverse(
                'posts:profile_unfollow',
                kwargs={'username': 'Author'}
            )
        )
        self.assertRedirects(
            response,
            reverse('posts:profile', kwargs={'username': 'Author'})
        )
        self.assertEqual(Follow.objects.count(), follow_count - 1)

    def test_new_post_followers(self):
        """Новый пост автора появляется в ленте у подписчиков"""
        response = self.authorized_client2.get(
            reverse('posts:follow_index')
        )
        old_context = response.context['page_obj']
        self.assertEqual(len(old_context), 1)
        self.assertEqual(old_context[0], self.post1)
        post2 = Post.objects.create(
            author=self.author,
            text='Тестовый текст 2',
        )
        response = self.authorized_client2.get(
            reverse('posts:follow_index')
        )
        new_context = response.context['page_obj']
        self.assertEqual(len(new_context), 2)
        self.assertEqual(new_context[0], post2)

    def test_no_new_post_unfollowers(self):
        """Новый пост не появляется у тех, кто не подписан"""
        response = self.authorized_client1.get(
            reverse('posts:follow_index')
        )
        old_context = response.context['page_obj']
        self.assertEqual(len(old_context), 0)
        Post.objects.create(
            author=self.author,
            text='Тестовый текст 2',
        )
        response = self.authorized_client1.get(
            reverse('posts:follow_index')
        )
        new_context = response.context['page_obj']
        self.assertEqual(len(new_context), 0)
