from django import forms


def validate_not_empty(value):
    """ Проверка на заполненность полей формы"""
    if value == '':
        raise forms.ValidationError(
            'Это поле обязательно для заполнения',
            params={'value': value},
        )
