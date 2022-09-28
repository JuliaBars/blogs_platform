from __future__ import annotations

from django.forms import ModelForm

from .models import Comment, Post


class PostForm(ModelForm):
    """Форма создания и редактирования поста"""
    class Meta:
        model = Post
        fields = ('text', 'group', 'image')
        help_texts = {
            'group': 'Выберите группу',
            'text': 'Введите сообщение',
            'image': 'Выберите иллюстрацию к посту',
        }
        labels = {
            'text': 'Текст сообщения',
            'group': 'Группа',
            'image': 'Иллюстрация для поста',
        }


class CommentForm(ModelForm):
    """Форма создания комментариев."""
    class Meta:
        model = Comment
        fields = ('text',)
        help_texts = {'text': 'Введите комментарий'}
        labels = {'text': 'Текст комментария'}
