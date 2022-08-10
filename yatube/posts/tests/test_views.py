import shutil
import tempfile

from django.contrib.auth import get_user_model
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django import forms
from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.cache import cache

from ..models import Group, Post, Follow, Comment


User = get_user_model()

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostPagesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        """Создаем фикстуры:

            user: неавторизованный пользователь,
            follow_user: автор из подписок,
            unfollow_user: пользователь без подписок,
            subscribe: PostCreator подписался на FollowingUser,
            group: новая группа,
            post: пост написанный PostCreator,
            new_post: пост написанный FollowingUser,
            uploaded: картинка для поста
        """
        cls.user = User.objects.create_user(username='PostCreator')
        cls.follow_user = User.objects.create_user(
            username='FollowingUser'
        )
        cls.unfollow_user = User.objects.create_user(
            username='UnfollowingUser'
        )
        cls.subscribe = Follow.objects.create(
            author=cls.follow_user,
            user=cls.user
        )
        cls.group = Group.objects.create(
            title='Название группы',
            description='Описание группы',
            slug='group-name-slug'
        )
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
            content_type='image/gif'
        )
        cls.new_post = Post.objects.create(
            author=cls.follow_user,
            text='Пост, созданный для проверки подписок',
            group=cls.group,
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Пост, созданный лишь для проверки кода',
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
        self.group_2 = Group.objects.create(slug='another-group-slug')
        self.posts_number = Post.objects.count()
        self.authorized_unfollower = Client()
        self.authorized_unfollower.force_login(PostPagesTests.unfollow_user)

        cache.clear()

    def url(self, url, **kwargs):
        return reverse(url, kwargs=kwargs)

    def test_pages_show_picture_in_context(self):
        """Шаблоны страниц передают в контексте изображение,
        загруженное пользователем."""
        urls = [
            self.url('posts:index'),
            self.url('posts:profile', username=self.user.username),
            self.url('posts:group_list', slug=self.group.slug),
        ]

        for url in urls:
            with self.subTest(url=url):
                response = self.authorized_client.get(url)
                post_context = response.context['page_obj'].object_list
                post_list = Post.objects.all()
                for post in response.context['page_obj'].object_list:
                    if post is self.post:
                        self.assertEqual(post_list[0].image, post_context[0].image)

    def test_new_post_page_show_correct_context(self):
        """Форма создания поста сформирована с правильным контекстом."""
        response = self.authorized_client.get(reverse('posts:post_create'))
        form_fields = {
            'group': forms.fields.ChoiceField,
            'text': forms.fields.CharField,
            'image': forms.fields.ImageField,
        }

        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_fields = response.context['form'].fields[value]
                self.assertIsInstance(form_fields, expected)

    def test_pages_uses_correct_template(self):
        """Во view-функциях используются правильные html-шаблоны."""
        urls = [
            self.url('posts:index'),
            self.url('posts:profile', username=self.user.username),
            self.url('posts:group_list', slug=self.group.slug),
            self.url('posts:post_detail', post_id=self.post.id),
            self.url('posts:post_create'),
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
            Post.objects.all()
        )

    def test_group_list_page_shows_correct_context(self):
        """Ожидаемый контекст group_list -
        список постов, отфильтрованных по группе."""
        response = self.authorized_client.get(
            self.url('posts:group_list', slug=self.group.slug)
        )
        self.assertIn(
            response.context['page_obj'].object_list[0],
            PostPagesTests.group.posts.all()
        )

    def test_profile_page_shows_correct_context(self):
        """Ожидаемый контекст profile -
        посты только выбранного автора."""
        response = self.authorized_client.get(
            self.url('posts:profile', username=self.user.username)
        )
        self.assertIn(
            response.context['page_obj'].object_list[0],
            PostPagesTests.user.posts.all()
        )

    def test_post_detail_page_show_correct_context(self):
        """Ожидаемый контекст post_detail -
        один пост, выбранный по id и картинка."""
        response = self.authorized_client.get(
            self.url('posts:post_detail', post_id=self.post.id)
        )
        first_post = response.context['post']
        post_text = first_post.text
        post_image = first_post.image
        self.assertEqual(post_text, PostPagesTests.post.text)
        self.assertEqual(post_image, PostPagesTests.post.image)

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
            self.url('posts:post_edit', post_id=self.post.id)
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
            self.url('posts:index'),
            self.url('posts:group_list', slug=self.group.slug),
            self.url('posts:profile', username=self.user.username),
        )
        for url in urls:
            with self.subTest(url=url):
                response = self.authorized_client.get(url)
            self.assertIn(
                response.context['page_obj'].object_list[0],
                Post.objects.all()
            )

    def test_new_post_absence(self):
        """Пост не попал в группу, для которой не был предназначен."""
        response = self.authorized_client.get(reverse('posts:index'))
        self.assertNotEqual(response.context.get('page_obj')[0].group,
                            self.group_2)

    def test_cach_in_index_page(self):
        """Проверяем кеширование главной страницы."""
        response = self.authorized_client.get(reverse('posts:index'))
        with_cache = response.content
        Post.objects.all().delete()
        response = self.authorized_client.get(reverse('posts:index'))
        after_clearing_the_cache = response.content
        self.assertEqual(
            with_cache,
            after_clearing_the_cache
        )
        cache.clear()
        response = self.authorized_client.get(reverse('posts:index'))
        after_clearing_the_cache = response.content
        self.assertNotEqual(
            with_cache,
            after_clearing_the_cache
        )

    def test_follow_index_page(self):
        """Если создать подписку,
        то посты на странице подписок авторизованного
        пользователя появляются."""
        response = self.authorized_client.get(reverse('posts:follow_index'))
        self.assertIn(
            response.context['page_obj'].object_list[0],
            Post.objects.all()
        )
    
    def test_unfollowing_clean_index_page(self):
        """Если отписаться,
        то посты исчезнут со страницы подписок."""
        response_before = self.authorized_client.get(reverse('posts:follow_index'))
        PostPagesTests.subscribe.delete()
        response_after = self.authorized_client.get(reverse('posts:follow_index'))
        self.assertNotEqual(response_before.content, response_after.content)

    def test_unfollow_index_page(self):
        """Если пользователь не подписан на автора, 
        то постов автора на странице его подписок нет."""
        response = self.authorized_unfollower.get(reverse('posts:follow_index'))
        self.assertNotIn(Post.objects.filter(
                author=PostPagesTests.follow_user,
                text='Пост, созданный для проверки подписок',
            ),
            response.context['page_obj'],  
        )


class PaginatorViewsTest(TestCase):
    """Тестируем паджинатор."""
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.group = Group.objects.create(
            title='Название группы',
            slug='group-name-slug'
        )
        cls.author = User.objects.create_user(username='post_author')
        cls.posts = []
        for i in range(14):
            cls.posts.append(Post.objects.create(
                text=f'Какой-то текст поста {i}',
                author=cls.author,
                group=cls.group
            ))

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(PaginatorViewsTest.author)
        cache.clear()

    def url(self, url, **kwargs):
        return reverse(url, kwargs=kwargs)

    def test_page_contains_not_more_than_ten_records(self):
        """Паджинатор выводит на одну страницу не более 10 постов."""
        reverse_url = {
            self.url('posts:index'): 10,
            self.url('posts:group_list', slug=self.group.slug): 10,
            self.url('posts:profile', username=self.author.username): 10,
            self.url(
                'posts:profile', username=self.author.username
            ) + '?page=2': 4,
        }
        for url, number_of_posts in reverse_url.items():
            response = self.authorized_client.get(url)
            with self.subTest(key=url):
                self.assertEqual(len(
                    response.context['page_obj']),
                    number_of_posts
                )