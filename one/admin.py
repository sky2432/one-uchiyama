from django.contrib import admin
from django.db.models import Q
from django.contrib import messages
from .models import Radio, Episode, Word
from .service.aws import transcribe_file, get_s3_path_from_url, get_transcript_json_from_s3, get_transcript_from_json, get_transcript_file_url
from .service.util import parse, now_datetime, is_hiragana
import environ

env = environ.Env()
env.read_env('.env')


class EpisodeAdmin(admin.ModelAdmin):
    actions = ['store_words_action', 'store_words_again_action']
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
                messages.warning(request, '単語保存済みのエピソードがあります。')
                return
        # 単語保存
        for episode in queryset:
            transcribe(episode, request)


    def store_words_again_action(self, request, queryset):
        # 単語未保存のエピソードが含まれていれば実行しない
        for episode in queryset:
            if not episode.word_stored:
                messages.warning(request, '単語未保存のエピソードがあります。')
                return
        for episode in queryset:
            print(episode.id)
            # 既存の単語を削除
            Word.objects.filter(episode_id=episode.id).delete()
            # 単語保存
            transcribe(episode, request)

    store_words_action.short_description = '初回単語保存'
    store_words_again_action.short_description = '再単語保存'


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
        # start_timeのキーがなければスキップ
        if 'start_time' not in item:
            continue

        # 単語を取得
        content = item['alternatives'][0]['content']

        # 2文字以下の「ひらがな」はスキップ
        if (len(content) <= 2 and is_hiragana(content)):
            continue

        # 原型または読みに部分一致
        words = Word.objects.order_by('id').filter(
            episode_id=episode_id,
            start_time__isnull=True
        ).filter(
            Q(original_form__contains=content) |
            Q(pronunciation__contains=content)
        )
        # 一致する最初の単語に開始時間を設定する
        if len(words):
            words[0].start_time = item['start_time']
            words[0].save()


admin.site.register(Radio)
admin.site.register(Episode, EpisodeAdmin)
admin.site.register(Word)
