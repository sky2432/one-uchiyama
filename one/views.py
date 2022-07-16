from django.shortcuts import render, get_object_or_404, redirect
from django.db.models import Q
from .models import Episode
from .service.util import parse


def top(request):
    return render(request, 'top.html')


def search(request):
    keyword = request.GET.get('keyword')
    episodes = Episode.objects.filter(
        Q(word__original_form__contains=keyword) | Q(word__pronunciation__contains=keyword)).distinct()
    return render(request, 'search.html', {'episodes': episodes, 'keyword': keyword})


def detail(request, pk):
    episode = get_object_or_404(Episode, pk=pk)
    return render(request, 'detail.html', {'episode': episode})
