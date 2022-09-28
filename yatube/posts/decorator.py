import collections
import decimal
import time
from typing import Any, Callable

from django.core.management import BaseCommand
from django.db import connection, reset_queries


def queries_stat(fn: Callable) -> Callable:

    def wrapper(*args: Any, **kwargs: Any) -> Any:
        reset_queries()
        # start_t = time.time()
        original_return = fn(*args, **kwargs)
        # print('TOTAL EXECUTION TIME:', time.time() - start_t)
        queries = connection.queries
        total_queries_time = decimal.Decimal(0)
        total_queries_count = 0
        stats: Any = collections.defaultdict(lambda: dict())
        for query in queries:
            total_queries_time += decimal.Decimal(query['time'])
            total_queries_count += 1
            if query['sql'] in stats:
                stats[query['sql']]['time'] += decimal.Decimal(query['time'])
                stats[query['sql']]['count'] += 1
            else:
                stats[query['sql']]['time'] = decimal.Decimal(query['time'])
                stats[query['sql']]['count'] = 1
        print(f'TOTAL QUERIES STATS. COUNT: {total_queries_count} TIME: {total_queries_time}')
        # print('TOP 10 QUERIES BY COUNT')
        # for sql, stat in sorted(stats.items(), key=lambda elem: elem[1]['count'], reverse=True)[:10]:
        #     print(stat['count'], sql)
        print('TOP 10 QUERIES BY TIME')
        for sql, stat in sorted(stats.items(), key=lambda elem: elem[1]['time'], reverse=True)[:10]:
            print(stat['time'], sql)
        # print('\n')
        return original_return

    return wrapper


def show_time(func: Callable) -> Callable:

    def wrapper(*args, **kwargs) -> Any:
        _self: BaseCommand = args[0]
        start_time = time.time()
        result = func(*args, **kwargs)
        message = f'Время выполнения функции {func.__name__}: {time.time() - start_time}'
        if isinstance(_self, BaseCommand):
            _self.stdout.write(message)
        else:
            print(message)
        return result

    return wrapper
