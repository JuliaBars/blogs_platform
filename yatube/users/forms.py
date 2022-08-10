from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import get_user_model

""" Для регистрации на сайте создаем собственную html форму
    на основе класса UserCreationForm """


User = get_user_model()


class CreationForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = User
        fields = ('first_name', 'last_name', 'username', 'email')
