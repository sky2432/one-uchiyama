from django.contrib import admin
from .models import Radio, Episode, Word
from .service.aws import transcribe_file, getS3PathFromUrl, get_transcript
from .service.util import parse


class EpisodeAdmin(admin.ModelAdmin):
    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        get_words(obj)


def get_words(episode):
    english_title = episode.radio_id.english_title
    file_url = transcribe_file(
        english_title + '_' + str(episode.number),
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


admin.site.register(Radio)
admin.site.register(Episode, EpisodeAdmin)
admin.site.register(Word)
