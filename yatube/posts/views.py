from __future__ import annotations

from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.cache import cache_page

from posts.models import Follow, Group, Post, User

# from .decorator import queries_stat
from .forms import CommentForm, PostForm

SELECT_LIMIT = 10  # Количество постов на страницу


def paginator(request, posts):
    """Настраиваем Paginator"""
    paginator = Paginator(posts, SELECT_LIMIT)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return page_obj


# @cache_page(20, key_prefix='index_page')
# @queries_stat
def index(request):
    posts = Post.objects.prefetch_related('group', 'author')
    context = {
        'page_obj': paginator(request, posts),
    }
    return render(request, 'posts/index.html', context)


def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
    posts = group.posts.select_related('author')
    context = {
        'group': group,
        'page_obj': paginator(request, posts),
    }
    return render(request, 'posts/group_list.html', context)


def profile(request, username):
    """Персональная страница авторизованного пользователя."""
    author = get_object_or_404(User, username=username)
    posts = author.posts.select_related('group')
    n_posts = posts.count()
    following = (
        request.user.is_authenticated
        and Follow.objects.filter(
            user=request.user,
            author=author,
        ).exists()
    )
    context = {
        'page_obj': paginator(request, posts),
        'author': author,
        'n_posts': n_posts,
        'following': following,
    }
    return render(request, 'posts/profile.html', context)


def post_detail(request, post_id):
    """Страница с постом пользователя."""
    post = get_object_or_404(Post, pk=post_id)
    n_posts = post.author.posts.count()
    form = CommentForm(request.POST or None)
    comments = post.comments.all()
    context = {
        'post': post,
        'n_posts': n_posts,
        'form': form,
        'comments': comments,
    }
    return render(request, 'posts/post_detail.html', context)


@login_required
def post_create(request):
    """Страница создания постов для авторизованных пользователей."""
    form = PostForm(request.POST or None, files=request.FILES or None)

    if not request.method == 'POST' or not form.is_valid():
        context = {
            'form': form,
        }
        return render(request, 'posts/create_post.html', context)

    post = form.save(commit=False)
    post.author = request.user
    post.save()
    return redirect('posts:profile', post.author)


@login_required
def post_edit(request, post_id):
    """Страница редактирования постов для авторизованных пользователей."""
    post = get_object_or_404(Post, id=post_id)

    form = PostForm(request.POST or None, instance=post)
    if request.method == 'GET':
        if request.user == post.author:
            return render(
                request,
                'posts/create_post.html',
                {
                    'form': form,
                    'is_edit': True,
                    'post': post
                }
            )
        return redirect('posts:post_detail', post_id=post.id)

    if request.method == 'POST':
        form = PostForm(
            request.POST,
            files=request.FILES or None,
            instance=post
        )
        if form.is_valid():
            form.save()
        return redirect('posts:post_detail', post_id=post.id)


@login_required
def add_comment(request, post_id):
    """Добавление комментариев к посту."""
    post = get_object_or_404(Post, id=post_id)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect('posts:post_detail', post_id=post_id)


@login_required
def follow_index(request):
    """Страница со списком постов из подписок пользователя."""
    post_list_follow = Post.objects.filter(
        author__following__user=request.user,
    )
    context = {
        'page_obj': paginator(request, post_list_follow),
    }
    return render(request, 'posts/follow.html', context)


@login_required
def profile_follow(request, username):
    """Подписка на автора со страницы его профиля."""
    author = get_object_or_404(User, username=username)
    if author != request.user:
        Follow.objects.get_or_create(user=request.user, author=author)

    return redirect('posts:profile', username=username)


@login_required
def profile_unfollow(request, username):
    """Отписка от автора."""
    author = get_object_or_404(User, username=username)
    Follow.objects.filter(
        user=request.user,
        author=author,
    ).delete()
    return redirect('posts:profile', username=username)
