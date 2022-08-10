from django.contrib.auth import get_user_model
from django.test import TestCase, Client
from django.urls import reverse

from http import HTTPStatus

from ..models import Group, Post

User = get_user_model()


class PostURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        """Создаем фикстуры:

            user: неавторизованный пользователь,
            author: авторизованный автор,
            not_author: авторизованный не автор,
            group: группа,
            post: пост
        """
        super().setUpClass()
        cls.user = User.objects.create_user(username='HasNoName')
        cls.author = User.objects.create_user(username='author')
        cls.not_author = User.objects.create_user(username='not_author')
        cls.group = Group.objects.create(
            title='Название группы',
            description='Описание группы',
            slug='group-name-slug'
        )
        cls.post = Post.objects.create(
            author=cls.author,
            text='Пост созданный лишь для проверки кода',
        )

    def setUp(self) -> None:
        """Создаем тестовых веб-клиентов:

            guest_client: неавторизованный пользователь,
            author_client: авторизованный автор поста,
            not_author_client: авторизованный не автор поста
        """
        self.guest_client = Client()
        self.author_client = Client()
        self.author_client.force_login(PostURLTests.author)
        self.not_author_client = Client()
        self.not_author_client.force_login(PostURLTests.not_author)

    def url(self, url, **kwargs):
        return reverse(url, kwargs=kwargs)

    def test_urls_and_templates_for_public_pages(self):
        """Публичные странички общедоступны
        и используют правильные шаблоны."""
        urls = [
            self.url('posts:index'),
            self.url('posts:group_list', slug=self.group.slug),
            self.url('posts:profile', username=self.user.username),
            self.url('posts:post_detail', post_id=self.post.id),
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

    def test_castome_pages_for_BadRequest_use_correct_template(self):
        """Кастомные странички ошибок
        используют правильные шаблоны."""
        response = self.guest_client.get('page_not_found')
        self.assertTemplateUsed(response, 'core/404.html')

    def test_private_pages_use_correct_template(self):
        """Странички с приватным доступом используют
        правильный шаблон."""
        urls = [
            self.url('posts:post_edit', post_id=self.post.id),
            self.url('posts:post_create'),
        ]

        for url in urls:
            with self.subTest(url=url):
                response = self.author_client.get(url)
                self.assertTemplateUsed(response, 'posts/create_post.html')

    def test_unexisting_page_404(self):
        """Несуществующая страница дает код 404."""
        response = self.guest_client.get('/unexisting_page/')
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

    def test_comment_page_for_authorized_only(self):
        """Комментировать посты может только 
        авторизованный пользователь."""
        response = self.not_author_client.get(
            f'/posts/{self.post.id}/comment/',
            follow=True
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_cooment_page_not_for_anonymous(self):
        """При попытке сделать комментарий неавторизовнный
        пользователь будет перенаправлен на страницу
        авторизации."""
        response = self.guest_client.get(
            f'/posts/{self.post.id}/comment/', follow=True
        )
        self.assertRedirects(
            response,
            f'{reverse("login")}?next='
            f'{reverse("posts:add_comment", kwargs={"post_id": self.post.id})}'
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
            response, '/auth/login/?next=/create/'
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
            f'/posts/{self.post.id}/edit/', follow=True
        )
        self.assertRedirects(
            response, f'/posts/{PostURLTests.post.id}/'
        )
