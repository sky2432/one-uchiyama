from django.shortcuts import render
from django.db.models import Q, Prefetch
from django.core.paginator import Paginator
from .models import Episode, Word
import math

from django.db.models.query import QuerySet
from django.core.handlers.wsgi import WSGIRequest
from django.http.response import HttpResponse

def top(request: WSGIRequest) -> HttpResponse:
    """トップページを表示する

    Args:
        request (WSGIRequest): Djangoリクエスト

    Returns:
        HttpResponse: Djangoレスポンス
    """
    return render(request, 'top.html')


def search(request: WSGIRequest) -> HttpResponse:
    """キーワードで回を検索する

    キーワードに部分一致した単語も同時に取得する。

    Args:
        request (WSGIRequest): Djangoリクエスト

    Returns:
        HttpResponse: Djangoレスポンス
    """
    keyword = request.GET.get('keyword')
    # Noneチェック
    if not keyword:
        keyword = ''

    episodes = Episode.objects.order_by('number').reverse().prefetch_related(
        Prefetch('word_set', queryset=Word.objects.order_by('start_time').filter(
            Q(original_form__contains=keyword) |
            Q(pronunciation__contains=keyword)
        ))).filter(
            Q(word__original_form__contains=keyword) |
            Q(word__pronunciation__contains=keyword)
        ).distinct()
    episodes = __add_start_time_minutes(episodes)

    # ページネーション
    per_page = 5
    paginator = Paginator(episodes, per_page)
    page_num = request.GET.get('page', 1)
    try:
        episodes = paginator.page(page_num)
    except Exception:
        episodes = paginator.page(1)

    return render(request, 'search.html', {'episodes': episodes, 'keyword': keyword})


def __add_start_time_minutes(episodes: QuerySet) -> QuerySet:
    """分単位の開始時間（00:00形式）を単語に追加する

    Args:
        episodes (QuerySet): Word情報を含んだEpisodeモデルのリスト
    Returns:
        QuerySet: Episodeモデルのリスト
    """
    for episode in episodes:
        for word in episode.word_set.all():
            time_float = word.start_time
            if time_float is None:
                continue
            elif time_float < 60:
                word.start_time_minutes = f'00:{str(int(time_float)).zfill(2)}'
            else:
                minutes = math.floor(time_float / 60)
                second = int(time_float % 60)
                word.start_time_minutes = f'{str(minutes).zfill(2)}:{str(second).zfill(2)}'
    return episodes
