from django.contrib import admin
from .models import Radio, Episode, Word, TemporaryWord
from .service.aws import transcribe_file, get_s3_path_from_url, get_transcript_from_s3
from .service.util import parse
import uuid
import environ


env = environ.Env()
env.read_env('.env')


class EpisodeAdmin(admin.ModelAdmin):
    def save_model(self, request, obj, form, change):
        """管理画面でエピソードを保存する。

        新規保存のとき
        またはオーディオファイルが変更された場合は、文字起こしを行い、単語を保存する。
        """
        episode = Episode.objects.filter(id=obj.id)
        if len(episode) == 0:
            print('new model')
            is_store = True
        elif obj.audio_file != episode[0].audio_file:
            print('edit model')
            is_store = True
            Word.objects.filter(episode_id=episode[0].id).delete()
        else:
            is_store = False

        super().save_model(request, obj, form, change)
        if is_store:
            get_words(obj)


def get_words(episode):
    english_title = episode.radio_id.english_title
    job_name = english_title + '_' + \
        str(episode.number) + '_' + str(uuid.uuid4())
    file_url = transcribe_file(
        job_name,
        get_s3_path_from_url(episode.audio_file.url,),
        english_title
    )
    transcript = get_transcript_from_s3(file_url)
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
admin.site.register(TemporaryWord)
