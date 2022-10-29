from django.contrib import admin
from .models import Radio, Episode, Word
from .service.aws import transcribe_file, get_s3_path_from_url, get_transcript_json_from_s3, get_transcript_from_json, get_transcript_file_url
from .service.util import parse, now_datetime
import environ
from django.contrib import messages

env = environ.Env()
env.read_env('.env')


class EpisodeAdmin(admin.ModelAdmin):
    actions = ['store_words_action']
    readonly_fields = ['word_stored']

    def save_model(self, request, obj, form, change):
        """管理画面でエピソードを保存する。

        新規保存のとき
        またはオーディオファイルが変更された場合は、文字起こしを行う。
        """
        episode = Episode.objects.filter(id=obj.id)
        is_store = False
        is_edit = False

        if len(episode) == 0:
            print('new model')
            is_store = True
        elif obj.audio_file != episode[0].audio_file:
            print('edit model')
            is_edit = True

        super().save_model(request, obj, form, change)

        if is_edit:
            # 単語保存フラグをリセット
            set_word_stored(episode[0], False)
            # 単語をリセット
            Word.objects.filter(episode_id=episode[0].id).delete()

        # 文字起こし実行
        if is_store or is_edit:
            start_transcript_job(obj)


    def store_words_action(self, request, queryset):
        # 単語保存済みエピソードが含まれていれば実行しない
        for episode in queryset:
            if episode.word_stored:
                messages.warning(request, '単語保存済みのエピソードがあります')
                return
        # 単語保存
        for obj in queryset:
            transcribe(obj, request)

    store_words_action.short_description = '単語を保存する'


def set_word_stored(episode, stored: bool):
    episode.word_stored = stored
    episode.save()


def start_transcript_job(episode):
    english_title = episode.radio_id.english_title
    job_name = english_title + '_' + str(episode.number) + '_' + now_datetime()
    transcribe_file(job_name, get_s3_path_from_url(episode.audio_file.url),english_title)
    # ジョブ名を保存
    store_job_name(episode.id, job_name)


def store_job_name(episodeId, job_name):
    episode = Episode.objects.get(id=episodeId)
    episode.job_name = job_name
    episode.save()


def transcribe(episode, request):
    episode = Episode.objects.get(id=episode.id)

    file_url = get_transcript_file_url(episode.job_name)
    if not file_url:
        messages.warning(request, '文字起こしが未完了です。時間を置いてから再度実行してください。')
        return

    transcript_json = get_transcript_json_from_s3(file_url)
    transcript = get_transcript_from_json(transcript_json)
    words = parse(transcript)
    store_words(words, episode)
    store_start_time(transcript_json['results']['items'], episode.id)
    set_word_stored(episode , True)
    messages.success(request, '単語の保存が完了しました')


def store_words(words, episode):
    """エピソードに単語を保存する

    Args:
        words (Word): Wordモデル
        episode (Episode): Episodeモデル
    """
    for word in words:
        Word.objects.create(
            episode_id=episode,
            original_form=word['original_form'],
            pronunciation=word['pronunciation'],
        )


def store_start_time(items, episode_id):
    """単語に開始時間を保存する

    Args:
        items (dict): 単語のjsonファイル
        episode_id (int): エピソードID
    """
    for item in items:
        if 'start_time' not in item:
            continue
        words = Word.objects.filter(
            episode_id=episode_id,
            original_form__contains=item['alternatives'][0]['content'],
            start_time__isnull=True
        )
        if len(words):
            words[0].start_time = item['start_time']
            words[0].save()


admin.site.register(Radio)
admin.site.register(Episode, EpisodeAdmin)
admin.site.register(Word)
