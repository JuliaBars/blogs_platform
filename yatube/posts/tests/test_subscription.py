from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse
from django.core.cache import cache

from posts.models import Group, Post, Follow


User = get_user_model()


class SubscriptionTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.leader_user = User.objects.create_user('leader')
        cls.follow_user = User.objects.create_user('following')
        cls.subscription = Follow.objects.create(
            author=cls.follow_user,
            user=cls.leader_user
        )
        cls.group = Group.objects.create(slug='group-slug')
        post = Post.objects.create
        cls.follower_post = post(author=cls.follow_user,
                                 text='пост подписчика', group=cls.group)
        cls.leader_post = post(author=cls.leader_user,
                               text='пост лидера', group=cls.group)

    def setUp(self):
        self.leader_client = Client()
        self.leader_client.force_login(SubscriptionTests.leader_user)
        self.follow_client = Client()
        self.follow_client.force_login(SubscriptionTests.follow_user)

        cache.clear()

    def test_follow_index_page(self):
        """Если создать подписку,
        то посты на странице подписок появляются."""
        response = self.leader_client.get(reverse('posts:follow_index'))
        self.assertIn(
            response.context['page_obj'].object_list[0],
            Post.objects.all()
        )

    def test_unfollowing_clean_index_page(self):
        """Если отписаться,
        то посты исчезнут со страницы подписок."""
        response_before = self.leader_client.get(
            reverse('posts:follow_index')
        )
        SubscriptionTests.subscription.delete()
        response_after = self.leader_client.get(
            reverse('posts:follow_index')
        )
        self.assertNotEqual(response_before.content, response_after.content)

    def test_unfollow_index_page(self):
        """Если пользователь не подписан на автора,
        то постов автора на странице его подписок нет."""
        response = self.follow_client.get(
            reverse('posts:follow_index')
        )
        self.assertNotIn(SubscriptionTests.leader_post,
                         response.context['page_obj'])
