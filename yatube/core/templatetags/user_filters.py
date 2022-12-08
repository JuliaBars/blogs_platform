from __future__ import annotations

from django import template

register = template.Library()


@register.filter
def addclass(field, css):
    """ Создаем свои фильтры для любого поля в HTML коде"""
    return field.as_widget(attrs={'class': css})
