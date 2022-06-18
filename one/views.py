from django.shortcuts import render, get_object_or_404, redirect
from django.db import transaction
from .models import Episode
from .service.aws import transcribe_file, getS3PathFromUrl


def top(request):
    return render(request, 'top.html')


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
            id=request.POST['id'],
            audio_file=request.FILES['audio_file'],
        )
        file_url = transcribe_file(
            'one-job', getS3PathFromUrl(episode.audio_file.url)
        )
