from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import Client, TestCase
from django.urls import reverse
from posts.models import Follow, Group, Post

from .factories import post_create

User = get_user_model()


class SubscriptionTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.leader_user = User.objects.create_user('leader')
        cls.follower = User.objects.create_user('follower')
        cls.subscription = Follow.objects.create(
            author=cls.leader_user,
            user=cls.follower
        )
        cls.group = Group.objects.create(slug='group-slug')
        cls.follower_post = post_create(cls.follower, cls.group)
        cls.leader_post = post_create(cls.leader_user, cls.group)

    def setUp(self):
        self.leader_client = Client()
        self.leader_client.force_login(SubscriptionTests.leader_user)
        self.follow_client = Client()
        self.follow_client.force_login(SubscriptionTests.follower)

        cache.clear()

    def test_follow_index_page(self):
        """Если создать подписку,
        то посты на странице подписок появляются."""
        response = self.follow_client.get(reverse('posts:follow_index'))
        self.assertIn(
            response.context['page_obj'].object_list[0],
            Post.objects.all()
        )

    def test_unfollowing_clean_index_page(self):
        """Если отписаться,
        то посты исчезнут со страницы подписок."""
        response_before = self.follow_client.get(
            reverse('posts:follow_index')
        )
        SubscriptionTests.subscription.delete()
        response_after = self.follow_client.get(
            reverse('posts:follow_index')
        )
        self.assertNotEqual(response_before.content, response_after.content)

    def test_unfollow_index_page(self):
        """Если пользователь не подписан на автора,
        то постов автора на странице его подписок нет."""
        response = self.leader_client.get(
            reverse('posts:follow_index')
        )
        self.assertNotIn(SubscriptionTests.follower_post,
                         response.context['page_obj'])
