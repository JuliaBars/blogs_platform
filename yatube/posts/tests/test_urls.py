from __future__ import annotations

from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import Client, TestCase
from django.urls import reverse
from core.views import page_not_found

from posts.models import Group, Post

from .factories import url_rev

User = get_user_model()


class PostURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user('user')
        cls.author = User.objects.create_user('author')
        cls.not_author = User.objects.create_user('not_author')
        cls.group = Group.objects.create(slug='group-slug')
        cls.post = Post.objects.create(author=cls.author, text='Пост автора')
        cls.wtf = page_not_found

    def setUp(self) -> None:
        self.guest_client = Client()
        self.author_client = Client()
        self.author_client.force_login(PostURLTests.author)
        self.not_author_client = Client()
        self.not_author_client.force_login(PostURLTests.not_author)

        cache.clear()

    def test_urls_and_templates_for_public_pages(self):
        """Публичные странички общедоступны
        и используют правильные шаблоны."""
        urls = [
            url_rev('posts:index'),
            url_rev('posts:group_list', slug=self.group.slug),
            url_rev('posts:profile', username=self.user.username),
            url_rev('posts:post_detail', post_id=self.post.id),
        ]

        templates = [
            'posts/index.html',
            'posts/group_list.html',
            'posts/profile.html',
            'posts/post_detail.html',
        ]

        for url, template in zip(urls, templates):
            with self.subTest(url=url):
                response = self.guest_client.get(url)
                self.assertTemplateUsed(response, template)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_bad_request_page_works_properly(self):
        """Несуществующая страница отдает код 404
        и кастомный шаблон."""
        response = self.guest_client.get('page_not_found')
        self.assertTemplateUsed(response, 'core/404.html')
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

    def test_private_pages_use_correct_template(self):
        """Странички с приватным доступом используют
        правильный шаблон."""
        urls = [
            url_rev('posts:post_edit', post_id=self.post.id),
            url_rev('posts:post_create'),
        ]

        for url in urls:
            with self.subTest(url=url):
                response = self.author_client.get(url)
                self.assertTemplateUsed(response, 'posts/create_post.html')

    def test_comment_page_for_authorized_only(self):
        """Комментировать посты может только
        авторизованный пользователь."""
        response = self.not_author_client.get(
            url_rev('posts:add_comment', post_id=self.post.id),
            follow=True,
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_cooment_page_not_for_anonymous(self):
        """При попытке оставить комментарий неавторизованный
        пользователь будет перенаправлен на страницу
        авторизации."""
        response = self.guest_client.get(
            url_rev('posts:add_comment', post_id=self.post.id),
            follow=True,
        )
        self.assertRedirects(
            response,
            f'{reverse("login")}?next='
            f'{reverse("posts:add_comment", kwargs={"post_id": self.post.id})}',
        )

    def test_create_url_exists_authorized(self):
        """Страница создания постов доступна авторизованному
        пользователю."""
        response = self.not_author_client.get('/create/')
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_create_url_redirect_anonymous_on_index(self):
        """Страница создания постов перенаправит анонимного
        пользователя на страницу авторизации."""
        response = self.guest_client.get('/create/', follow=True)
        self.assertRedirects(
            response, '/auth/login/?next=/create/',
        )

    def test_post_detail_edit_url_exist(self):
        """Страница редактирования поста доступна
        только автору этого поста."""
        response = self.author_client.get(f'/posts/{self.post.id}/edit/')
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_post_edit_url_redirect_anonymous_on_index(self):
        """Страница редактирования поста перенаправит
        не автора поста на страницу поста."""
        response = self.not_author_client.get(
            f'/posts/{self.post.id}/edit/', follow=True,
        )
        self.assertRedirects(
            response, f'/posts/{PostURLTests.post.id}/',
        )

    def test_very_bad_request_page_works_properly(self):
        """Несуществующая страница отдает код 404
        и кастомный шаблон."""
        response = self.guest_client.get(PostURLTests.wtf)
        print('\n>>>', response.request['PATH_INFO'])
        print('\n>>>', response.request)
        self.assertTemplateUsed(response, 'core/404.html')
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)