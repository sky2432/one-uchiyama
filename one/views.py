from django.shortcuts import render
from django.db.models import Q, Prefetch
from .models import Episode, Word
import math

def top(request):
    """_summary_

    Args:
        request (_type_): _description_

    Returns:
        _type_: _description_
    """
    return render(request, 'top.html')


def search(request):
    """キーワードで回を検索する。

    キーワードに部分一致した単語も同時に取得する。
    """
    keyword = request.GET.get('keyword')
    episodes = Episode.objects.order_by('number').reverse().prefetch_related(
        Prefetch('word_set', queryset=Word.objects.order_by('start_time').filter(
            Q(original_form__contains=keyword) |
            Q(pronunciation__contains=keyword)
        ))).filter(
            Q(word__original_form__contains=keyword) |
            Q(word__pronunciation__contains=keyword)
        ).distinct()
    episodes = __add_start_time_minutes(episodes)
    return render(request, 'search.html', {'episodes': episodes, 'keyword': keyword})


def __add_start_time_minutes(episodes):
    """分単位の開始時間（00:00形式）を単語に追加する

    Args:
        episodes (QuerySet[Episode]): Word情報を含んだEpisodeモデルのリスト
    Returns:
        QuerySet[Episode]: Episodeモデルのリスト
    """
    print(type(episodes))
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
