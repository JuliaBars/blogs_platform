from __future__ import annotations

from django import template

""" Создаем свои фильтры для любого поля в HTTML коде"""

register = template.Library()


@register.filter
def addclass(field, css):
    return field.as_widget(attrs={'class': css})
