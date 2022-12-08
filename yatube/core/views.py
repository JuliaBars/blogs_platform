from __future__ import annotations

from django.shortcuts import render


def page_not_found(request, exception):
    """Страница ошибки 404 отдает кастомный шаблон"""
    return render(request, 'core/404.html', {'path': request.path}, status=404)


def server_error(request):
    """Страница ошибки 500 отдает кастомный шаблон"""
    return render(request, 'core/500.html', status=500)


def permission_denied(request, exception):
    """Страница ошибки 403 отдает кастомный шаблон"""
    return render(request, 'core/403.html', status=403)


def csrf_failure(request, reason=''):
    """Страница ошибки 403csrf отдает кастомный шаблон"""
    return render(request, 'core/403csrf.html')
