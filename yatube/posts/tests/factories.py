import random
import string

from django.urls import reverse
from posts.models import Post


def random_string(length):
    letters = string.ascii_lowercase
    rand_string = ''.join(random.choice(letters) for i in range(length))
    return rand_string


def post_create(user, group):
    text = random_string(8)
    return Post.objects.create(text=text, author=user, group=group)


def url_rev(url, **kwargs):
    return reverse(url, kwargs=kwargs)
