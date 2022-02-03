from django.contrib.auth import get_user_model
from django.test import TestCase
from posts.models import COUNT_OF_CHAR

from ..models import Group, Post

User = get_user_model()


NUM_OF_CHAR_2: int = 30  # количество символов у поста


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.post = Post.objects.create(
            author=cls.user,
            text='Т' * NUM_OF_CHAR_2,
        )

    def test_post_models_have_correct_object_names(self):
        """Проверяем, что у моделей корректно работает __str__."""
        post = PostModelTest.post
        expected_post_text = post.text[:COUNT_OF_CHAR]
        self.assertEqual(expected_post_text, str(post))


class GroupModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовый заголовок',
            slug='test-slug',
            description='Тестовое описание группы',
        )

    def test_group_models_have_correct_object_names(self):
        """Проверяем, что у моделей group корректно работает __str__."""
        group = GroupModelTest.group
        expected_group_title = group.title
        self.assertEqual(expected_group_title, str(group))
