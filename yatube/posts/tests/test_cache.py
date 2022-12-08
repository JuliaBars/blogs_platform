from __future__ import annotations

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import Client, TestCase
from django.urls import reverse

from posts.models import Group, Post

from .factories import post_create

User = get_user_model()


class CacheTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='PostCreator')
        cls.group = Group.objects.create(slug='group-slug')
        cls.post = post_create(cls.user, cls.group)

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(CacheTests.user)

        cache.clear()

    def test_cach_in_index_page(self):
        response = self.authorized_client.get(reverse('posts:index'))
        with_cache = response.content
        Post.objects.all().delete()
        response = self.authorized_client.get(reverse('posts:index'))
        after_clearing_the_base = response.content
        self.assertEqual(
            with_cache,
            after_clearing_the_base,
        )
        cache.clear()
        response = self.authorized_client.get(reverse('posts:index'))
        after_clearing_the_cache = response.content
        self.assertNotEqual(
            with_cache,
            after_clearing_the_cache,
        )
