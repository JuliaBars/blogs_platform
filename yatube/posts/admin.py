from __future__ import annotations

from ckeditor.widgets import CKEditorWidget
from django.contrib import admin
from django.db import models

from .models import Comment, Follow, Group, Post


class PostAdmin(admin.ModelAdmin):
    list_display = ('pk', 'text', 'pub_date', 'author', 'group')
    list_editable = ('group',)
    search_fields = ('text',)
    list_filter = ('pub_date',)
    empty_value_display = '-пусто-'
    formfield_overrides = {
        models.TextField: {'widget': CKEditorWidget}
    }


admin.site.register(Post, PostAdmin)
admin.site.register(Group)


@admin.register(Follow)
class FollowAdmin(admin.ModelAdmin):
    list_display = ('user', 'author')


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ('post', 'author', 'text', 'created')
