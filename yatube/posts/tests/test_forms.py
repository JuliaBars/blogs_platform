import shutil
import tempfile

from posts.forms import PostForm
from posts.models import Group, Post, Comment
from django.contrib.auth import get_user_model
from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, override_settings, TestCase
from django.urls import reverse


User = get_user_model()
TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostCreateFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.group = Group.objects.create(
            title='Название группы',
            description='Описание группы',
            slug='group-name-slug'
        )
        cls.author = User.objects.create_user(username='author')
        cls.post = Post.objects.create(
            author=cls.author,
            text='Пост созданный для проверки кода',
        )
        cls.form = PostForm()

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(PostCreateFormTests.author)
        self.picture_for_post = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        self.uploaded = SimpleUploadedFile(
            name='Picture_for_post.gif',
            content=self.picture_for_post,
            content_type='image/gif'
        )

    def url(self, url, **kwargs):
        return reverse(url, kwargs=kwargs)

    def test_create_post(self):
        """Валидная форма создает новый пост
        и общее количество постов увеличивается на 1."""
        posts_count = Post.objects.count()
        form_data = {
            'text': 'Новый пост с новым текстом',
            'group': PostCreateFormTests.group.id,
            'image': self.uploaded,
        }
        self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        self.assertEqual(Post.objects.count(), posts_count + 1)
        self.assertTrue(
            Post.objects.filter(
                author=PostCreateFormTests.post.author,
                group=PostCreateFormTests.group.id,
                text='Новый пост с новым текстом',
                image='posts/Picture_for_post.gif'
            ).exists()
        )

    def test_edit_post(self):
        """Пост успешно редактируется."""
        form_data = {
            'text': 'Отредактированный пост',
            'group': PostCreateFormTests.group.id,
        }
        self.authorized_client.post(
            reverse('posts:post_edit', args=[PostCreateFormTests.post.id]),
            data=form_data,
            follow=True
        )
        self.assertTrue(
            Post.objects.filter(
                id=PostCreateFormTests.post.id,
                group=PostCreateFormTests.group,
                text='Отредактированный пост'
            ).exists()
        )

    def test_create_comment(self):
        """Комментарии к посту успешно создаются."""
        comments_count = Comment.objects.count()
        form_data = {'text': 'Новый комментарий'}
        self.authorized_client.post(
            reverse('posts:add_comment', args=[PostCreateFormTests.post.id]),
            data=form_data,
            follow=True
        )
        self.assertEqual(Comment.objects.count(), comments_count + 1)
        self.assertTrue(
            Comment.objects.filter(
                text='Новый комментарий',
            ).exists()
        )

    def test_group_cant_create_existing_slug(self):
        """Проверка уникальности поля slug."""
        groups_count = Group.objects.count()
        form_data = {
            'title': 'Заголовок группы',
            'slug': 'unique-slug',
        }
        response = self.guest_client.post(
            reverse('posts:index'),
            data=form_data,
            follow=True
        )
        self.assertEqual(Group.objects.count(), groups_count)
        self.assertEqual(response.status_code, 200)

    def test_post_text_cant_be_empty(self):
        """
            Проверка, что пост с пустым полем text
            не создается и выдает ошибку.
        """
        posts_count = Post.objects.count()
        form_data = {
            'text': '',
            'group': self.group,
        }
        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        self.assertEqual(Post.objects.count(), posts_count)
        self.assertFormError(
            response,
            'form',
            'text',
            ['Обязательное поле.']
        )
        self.assertEqual(response.status_code, 200)