from __future__ import annotations

from datetime import datetime


def year(request):
    """Добавляет переменную с текущим годом."""
    year = datetime.now().year
    return {
        'year': year,
    }
