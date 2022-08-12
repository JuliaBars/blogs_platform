from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse
from django.core.cache import cache

from posts.models import Group, Post, Follow


User = get_user_model()


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
        cls.new_post = Post.objects.create(
            author=cls.follow_user,
            text='Пост, созданный для проверки подписок',
            group=cls.group,
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Пост, созданный лишь для проверки кода',
            group=cls.group,
        )

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(PostPagesTests.user)
        self.group_2 = Group.objects.create(slug='another-group-slug')
        self.posts_number = Post.objects.count()
        self.authorized_unfollower = Client()
        self.authorized_unfollower.force_login(PostPagesTests.unfollow_user)

        cache.clear()

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
        response_before = self.authorized_client.get(
            reverse('posts:follow_index')
        )
        PostPagesTests.subscribe.delete()
        response_after = self.authorized_client.get(
            reverse('posts:follow_index')
        )
        self.assertNotEqual(response_before.content, response_after.content)

    def test_unfollow_index_page(self):
        """Если пользователь не подписан на автора,
        то постов автора на странице его подписок нет."""
        response = self.authorized_unfollower.get(
            reverse('posts:follow_index')
        )
        self.assertNotIn(Post.objects.filter(
            author=PostPagesTests.follow_user,
            text='Пост, созданный для проверки подписок',
        ),
            response.context['page_obj'],
        )
