from django.shortcuts import render, get_object_or_404, redirect
from django.db.models import Q, Prefetch
from .models import Episode, Word


def top(request):
    return render(request, 'top.html')


def search(request):
    """キーワードで回を検索する。

    キーワードに部分一致した単語も同時に取得する。
    """
    keyword = request.GET.get('keyword')
    episodes = Episode.objects.order_by('number').reverse().prefetch_related(
        Prefetch('word_set', queryset=Word.objects.filter(
            Q(original_form__contains=keyword) |
            Q(pronunciation__contains=keyword)
        ))).filter(
            Q(word__original_form__contains=keyword) |
            Q(word__pronunciation__contains=keyword)
        ).distinct()
    return render(request, 'search.html', {'episodes': episodes, 'keyword': keyword})
