from django.contrib.auth import get_user_model
from django.test import TestCase
from django.core.cache import cache

from ..models import Group, Post

User = get_user_model()


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='author')
        cls.group = Group.objects.create(slug='group-slug')
        cls.post = Post.objects.create(
            author=cls.user,
            group=cls.group,
            text='Не более 15 символов может поместиться в превью поста',
        )

    def setUp(self) -> None:
        cache.clear()

    def test_verbose_name(self):
        """Verbose_name в полях модели Post совпадает с ожидаемым."""
        post = PostModelTest.post
        field_verboses = {
            'text': 'Текст поста',
            'group': 'Группа',
            'author': 'Автор поста',
        }
        for field, expected_value in field_verboses.items():
            with self.subTest(field=field):
                self.assertEqual(
                    post._meta.get_field(field).verbose_name, expected_value)

    def test_verbose_name_group(self):
        """Verbose_name в полях модели Group совпадает с ожидаемым."""
        group = PostModelTest.group
        field_verboses = {
            'title': 'Название группы',
            'slug': 'Адрес url для группы',
            'description': 'Описание группы',
        }
        for field, expected_value in field_verboses.items():
            with self.subTest(field=field):
                self.assertEqual(
                    group._meta.get_field(field).verbose_name, expected_value)

    def test_help_text(self):
        """help_text в полях модели Post совпадает с ожидаемым."""
        post = PostModelTest.post
        field_help_texts = {
            'text': 'Напишите ваш пост',
            'group': 'Выберите группу для поста',
            'author': 'Выберите автора',
        }
        for field, expected_value in field_help_texts.items():
            with self.subTest(field=field):
                self.assertEqual(
                    post._meta.get_field(field).help_text, expected_value)

    def test_help_text_group(self):
        """help_text в полях модели Group совпадает с ожидаемым."""
        group = PostModelTest.group
        field_help_texts = {
            'title': 'Придумайте название группы',
            'slug': 'Придумайте человекочитаемый адрес',
            'description': 'Напишите о чём ваша группа',
        }
        for field, expected_value in field_help_texts.items():
            with self.subTest(field=field):
                self.assertEqual(
                    group._meta.get_field(field).help_text, expected_value)

    def test_post_str_returns_text_no_longer_15_symbols(self):
        self.assertEqual('Не более 15 сим', f'{PostModelTest.post}')

    def test_models_have_correct__str__(self):
        self.assertEqual(PostModelTest.group.title, str(PostModelTest.group))
