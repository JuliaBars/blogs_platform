from __future__ import annotations

import shutil
import tempfile

from django import forms
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from posts.models import Group, Post

from .factories import url_rev

User = get_user_model()

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostPagesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user('PostCreator')
        cls.group = Group.objects.create(slug='group-slug')
        cls.group_2 = Group.objects.create(slug='another-group-slug')
        cls.picture_for_post = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        cls.uploaded = SimpleUploadedFile(
            name='picture_for_post.gif',
            content=cls.picture_for_post,
            content_type='image/gif',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Пост юзера с картинкой',
            group=cls.group,
            image=cls.uploaded,
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT)

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(PostPagesTests.user)

        self.posts_number = Post.objects.count()

        cache.clear()

    def test_pages_show_picture_in_context(self):
        """Шаблоны страниц передают в контексте изображение,
        загруженное пользователем."""
        urls = [
            url_rev('posts:index'),
            url_rev('posts:profile', username=self.user.username),
            url_rev('posts:group_list', slug=self.group.slug),
        ]

        for url in urls:
            with self.subTest(url=url):
                response = self.authorized_client.get(url)
                post = response.context['page_obj'][0]
                self.assertEqual(post.image, 'posts/picture_for_post.gif')

    def test_post_detail_page_show_correct_context(self):
        """Ожидаемый контекст post_detail -
        один пост, выбранный по id и картинка."""
        response = self.authorized_client.get(
            url_rev('posts:post_detail', post_id=self.post.id),
        )
        first_post = response.context['post']
        post_text = first_post.text
        post_image = first_post.image
        self.assertEqual(post_text, PostPagesTests.post.text)
        self.assertEqual(post_image, PostPagesTests.post.image)

    def test_pages_uses_correct_template(self):
        """Во view-функциях используются правильные html-шаблоны."""
        urls = [
            url_rev('posts:index'),
            url_rev('posts:profile', username=self.user.username),
            url_rev('posts:group_list', slug=self.group.slug),
            url_rev('posts:post_detail', post_id=self.post.id),
            url_rev('posts:post_create'),
        ]

        templates = [
            'posts/index.html',
            'posts/profile.html',
            'posts/group_list.html',
            'posts/post_detail.html',
            'posts/create_post.html',
        ]

        for url, template in zip(urls, templates):
            with self.subTest(url=url):
                response = self.authorized_client.get(url)
                self.assertTemplateUsed(response, template)

    def test_index_page_shows_correct_context(self):
        """Ожидаемый контекст index - список постов."""
        response = self.authorized_client.get(reverse('posts:index'))
        self.assertIn(
            response.context['page_obj'].object_list[0],
            Post.objects.all(),
        )

    def test_group_list_page_shows_correct_context(self):
        """Ожидаемый контекст group_list -
        список постов, отфильтрованных по группе."""
        response = self.authorized_client.get(
            url_rev('posts:group_list', slug=self.group.slug),
        )
        self.assertIn(
            response.context['page_obj'].object_list[0],
            PostPagesTests.group.posts.all(),
        )

    def test_profile_page_shows_correct_context(self):
        """Ожидаемый контекст profile -
        посты только одного автора."""
        response = self.authorized_client.get(
            url_rev('posts:profile', username=self.user.username),
        )
        self.assertIn(
            response.context['page_obj'].object_list[0],
            PostPagesTests.user.posts.all(),
        )

    def test_create_post_page_show_correct_context(self):
        """Ожидаемый контекст create_post -
        форма создания поста."""
        response = self.authorized_client.get(reverse('posts:post_create'))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_post_edit_page_show_correct_context(self):
        """Ожидаемый контекст post_edit -
        форма редактирования поста с указанным id."""
        response = self.authorized_client.get(
            url_rev('posts:post_edit', post_id=self.post.id),
        )
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_new_post_exists(self):
        """Новый пост отображается на указанных страницах."""
        urls = (
            url_rev('posts:index'),
            url_rev('posts:group_list', slug=self.group.slug),
            url_rev('posts:profile', username=self.user.username),
        )
        for url in urls:
            with self.subTest(url=url):
                response = self.authorized_client.get(url)
            self.assertIn(
                response.context['page_obj'].object_list[0],
                Post.objects.all(),
            )

    def test_new_post_absence(self):
        """Пост не попал в группу, для которой не был предназначен."""
        response = self.authorized_client.get(reverse('posts:index'))
        self.assertNotEqual(
            response.context.get('page_obj')[0].group,
            self.group_2,
        )
