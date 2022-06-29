from django.shortcuts import render, get_object_or_404, redirect
from django.db import transaction
from django.db.models import Q
from .models import Radio, Episode, Word
from .service.aws import transcribe_file, getS3PathFromUrl, get_transcript
from .service.util import parse


def top(request):
    return render(request, 'top.html')


def search(request):
    if request.method == 'POST':
        keyword = request.POST['keyword']
        episodes = Episode.objects.filter(
            Q(word__original_form__contains=keyword) | Q(word__pronunciation__contains=keyword)).distinct()
        return render(request, 'search.html', {'episodes': episodes})
    else:
        return redirect('top')


def detail(request, pk):
    episode = get_object_or_404(Episode, pk=pk)
    return render(request, 'detail.html', {'episode': episode})


def admin(request):
    if request.method == 'POST':
        admin_post(request)
        return redirect('top')
    else:
        return render(request, 'admin/store.html')


def admin_post(request):
    with transaction.atomic():
        episode = Episode.objects.create(
            radio_id=get_object_or_404(Radio, pk=request.POST['id']),
            number=request.POST['number'],
            audio_file=request.FILES['audio_file'],
            air_date=request.POST['air_date'],
        )
        english_title = episode.radio_id.english_title
        file_url = transcribe_file(
            english_title + '_' + episode.number,
            getS3PathFromUrl(episode.audio_file.url,),
            english_title
        )
        transcript = get_transcript(file_url)
        words = parse(transcript)
        store_words(words, episode)


def store_words(words, episode):
    for word in words:
        Word.objects.create(
            episode_id=episode,
            original_form=word['original_form'],
            pronunciation=word['pronunciation'],
        )
