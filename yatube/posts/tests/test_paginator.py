from __future__ import annotations

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import Client, TestCase

from posts.models import Group, Post

from .factories import url_rev

User = get_user_model()


class PaginatorViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.group = Group.objects.create(
            title='Новая группа',
            slug='group-slug',
        )
        cls.author = User.objects.create_user('post_author')
        Post.objects.bulk_create(
            Post(
                text=f'Текст нового поста {i}',
                author=cls.author,
                group=cls.group,
            ) for i in range(14)
        )

    def setUp(self):
        self.authorized_author = Client()
        self.authorized_author.force_login(PaginatorViewsTest.author)

        cache.clear()

    def test_page_contains_not_more_than_ten_records(self):
        """Паджинатор выводит на одну страницу не более 10 постов."""
        reverse_url = {
            url_rev('posts:index'): 10,
            url_rev('posts:group_list', slug=self.group.slug): 10,
            url_rev('posts:profile', username=self.author.username): 10,
            url_rev(
                'posts:profile', username=self.author.username,
            ) + '?page=2': 4,
        }
        for url, number_of_posts in reverse_url.items():
            response = self.authorized_author.get(url)
            with self.subTest(key=url):
                self.assertEqual(
                    len(
                        response.context['page_obj'],
                    ),
                    number_of_posts,
                )
