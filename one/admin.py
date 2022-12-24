from django.contrib import admin
from django.db.models import Q
from django.contrib import messages
from .models import Radio, Episode, Word
from .service.aws import transcribe_file, get_s3_path_from_url, get_transcript_json_from_s3, get_transcript_from_json, get_transcript_file_url
from .service.util import parse, now_datetime, is_hiragana
import environ

from django.core.handlers.wsgi import WSGIRequest
from django.db.models.query import QuerySet

env = environ.Env()
env.read_env('.env')

class EpisodeAdmin(admin.ModelAdmin):
    actions = ['store_words_action', 'store_words_again_action']
    readonly_fields = ['word_stored']

    def save_model(self, request: WSGIRequest, obj: Episode, form, change: bool) -> None:
        """管理画面でエピソードを保存する。

        新規保存のとき
        またはオーディオファイルが変更された場合は、文字起こしを行う。

        Args:
            request (WSGIRequest): Djangoリクエスト
            obj (Episode): Episodeモデル
            form (EpisodeForm): フォームのhtml
            change (bool): 変更があるかどうか
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


    def store_words_action(self, request: WSGIRequest, queryset: QuerySet) -> None:
        """単語未保存のエピソードに単語を保存する

        Args:
            request (WSGIRequest): Djangoリクエスト
            queryset (QuerySet): Episodeオブジェクト
        """
        print(type(request), type(queryset))
        # 単語保存済みエピソードが含まれていれば実行しない
        for episode in queryset:
            if episode.word_stored:
                messages.warning(request, '単語保存済みのエピソードがあります。')
                return
        # 単語保存
        for episode in queryset:
            transcribe(episode, request)
            messages.success(request, '単語の保存が完了しました')

    def store_words_again_action(self, request: WSGIRequest, queryset: QuerySet) -> None:
        """単語を再保存する

        Args:
            request (WSGIRequest): Djangoリクエスト
            queryset (QuerySet): Episodeオブジェクト
        """
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
            messages.success(request, '単語の再保存が完了しました')


    store_words_action.short_description = '初回単語保存'
    store_words_again_action.short_description = '再単語保存'


def set_word_stored(episode: Episode, stored: bool) -> None:
    """エピソードの単語保存ステータスを変更する

    Args:
        episode (Episode): Episodeモデル
        stored (bool): 保存済み: True, 未保存: False
    """
    episode.word_stored = stored
    episode.save()


def start_transcript_job(episode: Episode) -> None:
    """非同期で文字起こし処理を開始する

    Args:
        episode (Episode): Episodeモデル
    """
    english_title = episode.radio_id.english_title
    job_name = english_title + '_' + str(episode.number) + '_' + now_datetime()
    transcribe_file(job_name, get_s3_path_from_url(episode.audio_file.url), english_title)
    # ジョブ名を保存
    store_job_name(episode.id, job_name)


def store_job_name(episodeId: int, job_name: str) -> None:
    """対象エピソードに文字起こしジョブ名を保存する

    Args:
        episodeId (int): エピソードID
        job_name (str): transcribeジョブ名
    """
    episode = Episode.objects.get(id=episodeId)
    episode.job_name = job_name
    episode.save()


def transcribe(episode: Episode, request: WSGIRequest) -> None:
    """aws transcribeで文字起こししたファイルをmecabで解析し単語として保存する

    Args:
        episode (Episode): Episodeモデル
        request (WSGIRequest): Djangoリクエスト
    """
    episode = Episode.objects.get(id=episode.id)

    # 文字起こしファイルのURLを取得
    file_url = get_transcript_file_url(episode.job_name)
    if not file_url:
        messages.warning(request, '文字起こしが未完了です。時間を置いてから再度実行してください。')
        return

    # URLを元にS3からjsonファイルを取得
    transcript_json = get_transcript_json_from_s3(file_url)
    transcript = get_transcript_from_json(transcript_json)

    # 文字起こし文を形態素解析し、単語として保存する
    words = parse(transcript)
    store_words(words, episode)
    # 単語に開始時間を設定
    store_start_time(transcript_json['results']['items'], episode.id)

    # エピソードを「単語保存済み」にする
    set_word_stored(episode , True)


def store_words(words: list[dict[str, str]], episode: Episode) -> None:
    """エピソードに単語を保存する

    Args:
        words (list[dict[str, str]]): 形態素解析で取得した単語リスト
        episode (Episode): Episodeモデル
    """
    for word in words:
        Word.objects.create(
            episode_id=episode,
            original_form=word['original_form'],
            pronunciation=word['pronunciation'],
        )


def store_start_time(items: list[dict[str, str]], episode_id: int) -> None:
    """単語に開始時間を保存する

    Args:
        items (list[dict[str, str]]): 単語のjsonファイル
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
